import os, json, tempfile, shutil
from enum import Enum
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores.chroma import Chroma
from langchain_community.document_loaders.json_loader import JSONLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter


class JSONLoaderType(Enum):
    """
    Enum class for the JSONLoader type
    """

    UNSTRUCTURED = "unstructured"
    CLAUDE = "claude"


def load_unstructured_json(json_file: str):
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

    docs = loader.load()

    # Clean up the temporary file
    os.unlink(temp_file_path)
    return docs


def load_claude_json(json_file: str):
    """
    This function is used to convert the JSON file to Documents
    """

    def metadata_func(record: dict, metadata: dict) -> dict:
        metadata["source"] = record.get("source")
        metadata["page"] = record.get("page")
        return metadata

    loader = JSONLoader(
        file_path=json_file,
        jq_schema=".[]",
        content_key="page_content",
        metadata_func=metadata_func,
    )
    documents = loader.load()
    print("Loaded claude json file with", len(documents), "documents")

    # Split the text into chunks
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=400,
        chunk_overlap=100,
        separators=["\n\n", "\n", " ", ""],
    )

    chunked_docs = text_splitter.split_documents(documents)
    print("Chunked claude json file into", len(chunked_docs), "chunks")

    return chunked_docs


def create_vector_db(
    json_dir: str,
    persist_directory: str,
    loader_type: JSONLoaderType,
):
    """
    Create a VectorDB from the JSON data

    Args:
    -----
        json_dir: Path to the directory containing the JSON files
        loader_type: Type of JSON loader to use (unstructured or claude)
        persist_directory: Path to the directory to save the VectorDB

    Returns:
    --------
        VectorDB
    """

    chunked_docs = []
    for file in os.listdir(json_dir):
        if not file.endswith(".json"):
            continue
        if loader_type == JSONLoaderType.UNSTRUCTURED:
            chunked_docs.extend(load_unstructured_json(f"{json_dir}/{file}"))
        elif loader_type == JSONLoaderType.CLAUDE:
            chunked_docs.extend(load_claude_json(f"{json_dir}/{file}"))
        print(f"Loaded {file}\n")
    print("Loaded all JSON files with a total of", len(chunked_docs), "chunks")
    if os.path.basename(json_dir) == "uploaded":
        shutil.rmtree(json_dir)

    os.makedirs(persist_directory, exist_ok=True)
    try:
        client = Chroma()
        vectordb = client.from_documents(
            persist_directory=persist_directory,
            documents=chunked_docs,
            embedding=OpenAIEmbeddings(model="text-embedding-3-small"),
        )
    except Exception as e:
        print(f"An error occurred while creating the VectorDB: {e}")
        return None
    print("VectorDB created and saved.")
    print("Num of vectors:", vectordb._collection.count(), "\n")


# create_vector_db(
#     "data/RAG_LAW/unstructured", "data/RAG_LAW/vectordb", JSONLoaderType.UNSTRUCTURED
# )
