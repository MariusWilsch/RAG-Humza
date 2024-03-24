import json, datetime, os, io, tempfile
from unstructured_client import UnstructuredClient
from unstructured_client.models import shared, errors
from langchain_community.document_loaders.json_loader import JSONLoader
from langchain_community.vectorstores.chroma import Chroma
from langchain_openai import OpenAIEmbeddings
import pandas as pd

from langchain.schema import Document
from pprint import pprint

unstucturedCli = UnstructuredClient(
    api_key_auth="QgQU4SrWFfbgNbgmanPwtzQqEMJJwi",
    server_url="https://veloxforce-91m678wr.api.unstructuredapp.io",
)


def convert_html_table_to_csv(html_string: str):
    # Wrap the HTML string in a StringIO object
    html_string_io = io.StringIO(html_string)

    # Read the HTML table from the StringIO object into a DataFrame
    df = pd.read_html(html_string_io)[0]

    # Create a StringIO object to capture the CSV output
    csv_output = io.StringIO()

    # Write the DataFrame to the StringIO object as CSV
    df.to_csv(csv_output, index=False)

    # Get the CSV-formatted string from the StringIO object
    csv_string = csv_output.getvalue()

    # Possibliy save it or something, idk yet

    print(csv_string)


def UnstructuredStrategy(file_path: str):
    """
    Load the documents using the Unstructured API. This strategy is used for documents that contain text, mathematical formulas like LaTex and tables.
    According to my research this API is made for complex documents and also offers additional features like cleaning

    Notes
      Did not extraxt the Math Formula, didn't check if it works well with tables (21.03.2024)
      It works well with text and tables. I think this strategy can be used for anything that is not a math formula. (21.03.2024, 4pm)

    Returns:
      Chunks sorted by title
    """
    # Load the document
    print(f"Loading the document {file_path}")
    filename = os.path.basename(file_path)

    with open(file_path, "rb") as file:
        files = shared.Files(
            content=file.read(),
            file_name=filename,
        )
    # Fast strategy is for simple documents
    # request = shared.PartitionParameters(
    #     files=files,
    #     strategy="fast",
    #     split_pdf_page=True,
    #     max_characters="1750",
    #     new_after_n_chars="750",
    #     combine_under_n_chars="500",
    # )
    # Hi_res strategy is for complex documents with tables
    # model names, "chipper" or "yolox" or yolox_quantized
    request = shared.PartitionParameters(
        files=files,
        strategy="hi_res",
        pdf_infer_table_structure=True,
        split_pdf_page=True,
        languages=["eng"],
        chunking_strategy="by_title",
        max_characters="1750",
        new_after_n_chars="1000",
        combine_under_n_chars="500",
        hi_res_model_name="yolox_quantized",
    )
    try:
        response = unstucturedCli.general.partition(request)
        os.makedirs("unstructured", exist_ok=True)
        now = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        if filename.endswith(".pdf"):
            filename = filename[:-4]
        with open(f"unstructured/{filename + now}.json", "w") as f:
            json.dump(response.elements, f, indent=2)
        print(f"Document {file_path} was successfully loaded and chunked")
    except errors.SDKError as e:
        print(f"An error occurred while using the Unstructured API: {e}")
    except Exception as e:
        print(f"An error occurred while using the Unstructured API: {e}")


def call_strategy_on_folder(folder_path: str):
    """
    Call the UnstructuredStrategy for each file in the folder

    Args:
      folder_path: Path to the folder containing the documents
    """
    for file in os.listdir(folder_path):
        UnstructuredStrategy(f"{folder_path}/{file}")


def load_unstructured_json_data(json_file: str):
    """
    Load the JSON data from the Unstructured API
    Args:
        json_file: Path to the JSON file
    """
    with open(json_file, "r") as file:
        json_data = json.load(file)

    # Modify the JSON data
    for record in json_data:
        if record.get("type") == "Table":
            text_as_html = record.get("metadata", {}).get("text_as_html", "")
            record["text"] += f"\n{text_as_html}"

    # Save the modified JSON data to a temporary file
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as temp_file:
        json.dump(json_data, temp_file)
        temp_file_path = temp_file.name

    # Define the metadata extraction function
    def metadata_func(record: dict, metadata: dict) -> dict:
        # Extract the specified keys from the nested "metadata" key
        specified_keys = ["filetype", "page_number", "filename"]
        for key in specified_keys:
            if key in record.get("metadata", {}):
                metadata[key] = record["metadata"][key]

        return metadata

    loader = JSONLoader(
        file_path=temp_file_path,
        metadata_func=metadata_func,
        jq_schema=".[]",
        content_key="text",
    )

    # Load the data using the JSONLoader
    data = loader.load()
    # Clean up the temporary file
    os.unlink(temp_file_path)

    return data


def create_vector_db_from_unstructured(json_dir: str):
    """
    Create a VectorDB from the JSON data

    Args:
    -----
        json_dir: Path to the directory containing the JSON files

    Returns:
    --------
        VectorDB
    """

    chunked_docs = []
    for file in os.listdir(json_dir):
        if file.endswith(".json"):
            chunked_docs.extend(load_unstructured_json_data(f"{json_dir}/{file}"))
        print(f"Loaded {file}")
    print("Loaded all JSON files with a total of", len(chunked_docs), "chunks")

    # client = Chroma()
    # try:
    #     vectordb = client.from_documents(
    #         documents=chunked_docs,
    #         embedding=OpenAIEmbeddings(model="text-embedding-3-small"),
    #         persist_directory="data/vectordb/try2/vectordb",
    #     )
    # except Exception as e:
    #     print(f"An error occurred while creating the VectorDB: {e}")
    #     return None
    # print("VectorDB created and saved.")
    # print("Num of vectors:", vectordb._collection.count(), "\n")


# convert_html_table_to_csv()

# Call on multiple files
# call_strategy_on_folder("data/claude_output/2024-03-23-16-07-05/failed")

# Call on a single file
UnstructuredStrategy("data/raw_pdfs/5_Formula_The Mathematics of Real Estate.pdf")

# Load the JSON data
# load_unstructured_json_data(
#     "unstructured/smallerChunks_soft_limit_500_chars/4_SQUARE FOOTAGE - ANSI Z765 20212024-03-23_19-38-47.json"
# )

# Create a VectorDB from the JSON data
# create_vector_db_from_unstructured("unstructured/smallerChunks_soft_limit_500_chars")
