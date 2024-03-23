import json, datetime, os
from unstructured_client import UnstructuredClient
from unstructured_client.models import shared, errors
from langchain_community.document_loaders import UnstructuredPDFLoader

unstucturedCli = UnstructuredClient(
    api_key_auth="QgQU4SrWFfbgNbgmanPwtzQqEMJJwi",
    server_url="https://veloxforce-91m678wr.api.unstructuredapp.io",
)


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
    # )
    # Hi_res strategy is for complex documents with tables
    # model names, "chipper" and "yolox"
    request = shared.PartitionParameters(
        files=files,
        strategy="hi_res",
        pdf_infer_table_structure=True,
        split_pdf_page=True,
        languages=["eng"],
        chunking_strategy="by_title",
        combine_under_n_chars=500,
        hi_res_model_name="chipper",
    )
    try:
        response = unstucturedCli.general.partition(request)
        os.makedirs("unstructured", exist_ok=True)
        with open(f"unstructured/{filename}.json", "w") as f:
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
        if file.endswith(".pdf"):
            UnstructuredStrategy(f"{folder_path}/{file}")
        else:
            print(f"{file} is not a pdf file")


# call_strategy_on_folder("data/vectordb/try2/pdf_for_try_2")
UnstructuredStrategy(
    "/Users/verdant/RAG-Humza/data/raw_pdfs/6_Formula_Real Estate Appraisal Formulas.pdf"
)
