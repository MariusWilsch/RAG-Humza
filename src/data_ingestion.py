import os, json, pprint, shutil, datetime, anthropic, base64, yaml
from dataclasses import dataclass
from anthropic import APIError
from anthropic.resources.messages import Message
from typing import List
from io import BytesIO
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import chroma
from langchain.schema.document import Document
from pdf2image import convert_from_path
from unstructured_client import UnstructuredClient
from unstructured_client.models import shared, errors
from dotenv import load_dotenv

# Gloabls - Later convert that in to app.config.yaml
chunk_size = 500
chunk_overlap = 100
embedding_model = "text-embedding-3-small"


@dataclass
class LLM_Config:
    system_prompt1: str
    system_prompt2: str
    system_prompt3: str
    OPENAI_Chat_Model: str
    ClaudeAI_Chat_Model: str
    Claude_system_prompt: str
    OPENAI_Embedding_Model: str
    Chunk_Size: int
    Chunk_Overlap: int


@dataclass
class Config:
    LLM_Config: LLM_Config


# Get the config
with open("config/config.yml", "r") as f:
    data = yaml.safe_load(f)

config = Config(LLM_Config(**data["LLM_Config"]))

load_dotenv()

unstucturedCli = UnstructuredClient(
    api_key_auth="QgQU4SrWFfbgNbgmanPwtzQqEMJJwi",
    server_url="https://veloxforce-91m678wr.api.unstructuredapp.io",
)


# Convert this into a class using the STRATEGY Design pattern
class DataIngestion:
    """Class to read out text, formulas and possibilty text from pdfs and word documents. It embdes it and then uploads it to a vector database."""

    def __init__(self, folder_path: str) -> None:
        """
        Initialize the DataIngestion instance.

        Parameters:
            folder_path (str): The directory containing the documents.
            document (List[str]): A list of loaded documents.
        """

        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", " ", ""],
        )
        self.embedding_engine = OpenAIEmbeddings(model=embedding_model)
        self.chromaCli = chroma.Chroma()
        self.folder_path = folder_path

    def BasicTextStrategy(self) -> List:
        """
        Load the documents using the a basic PDF Loader, i.e PyMuPDF. This strategy is used for documents that are mostly text.
        It does not work well with table and mathematical formulas like LaTex.

        Returns:
          List[Doucment]: A list of loaded documents with metadata.
        """
        docs = []
        docs_cnt = 0
        document_dir = os.listdir(self.folder_path)
        for file in document_dir:
            # Joining the filename with the path to the file
            filepath = os.path.join(self.folder_path, file)
            if file.endswith(".json"):
                docs.extend(self.load_docs_from_json(filepath))
                docs_cnt += 1
                continue
            if not file.endswith(".pdf"):
                continue
            # Reading out the text using PyMuPDF
            try:
                docs.extend(PyMuPDFLoader(filepath).load())
                docs_cnt += 1
            except Exception as e:
                print(f"Error reading {file} with Error: {e}")
                return
        print("Number of loaded documents:", docs_cnt)
        print("Number of docs in list:", len(docs))
        return docs

    def chunk_documents(self, documents) -> List:
        """
        Chunk the documents into smaller pieces.

        Parameters:
          documents: The documents to chunk.

        Returns:
          List: The chunked documents.
        """
        print("Chunking documents...")
        chunked_docs = self.text_splitter.split_documents(documents)
        print("Number of chunks:", len(chunked_docs), "\n\n")
        return chunked_docs

    def prep_and_save_vectordb(self) -> None:
        """
        Embeds and saves the documents to the VectorDB.

        Parameters:
          documents (List): The chunked documents to embed.

        Returns:
          Chroma: The created VectorDB in a persist directory.
        """
        docs = []
        docs = self.BasicTextStrategy()
        chunked_docs = self.chunk_documents(docs)
        print("Embedding and saving docs to vectorDB...")
        # Deleting the prev vectorDB
        if os.path.exists("data/vectordb"):
            shutil.rmtree("data/vectordb")
        try:
            vectordb = self.chromaCli.from_documents(
                documents=chunked_docs,
                embedding=self.embedding_engine,
                persist_directory="data/vectordb",
            )
        except Exception as e:
            print(f"An error occurred while creating the VectorDB: {e}")
            return None
        print("VectorDB created and saved.")
        print("Num of vectors:", vectordb._collection.count(), "\n")
        return vectordb

    def UnstructuredStrategy(self, file_path: str):
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
        with open(file_path, "rb") as file:
            files = shared.Files(
                content=file.read(),
                file_name="example.pdf",
            )
        # Fast strategy is for simple documents
        # request = shared.PartitionParameters(
        #     files=files,
        #     strategy="fast",
        #     split_pdf_page=True,
        # )
        # Hi_res strategy is for complex documents with tables
        request = shared.PartitionParameters(
            files=files,
            strategy="hi_res",
            pdf_infer_table_structure=True,
            split_pdf_page=True,
            languages=["eng"],
        )
        try:
            response = unstucturedCli.general.partition(request)
            filename = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            with open(f"unstructured/{filename}.json", "w") as f:
                json.dump(response.elements, f, indent=2)
        except errors.SDKError as e:
            print(f"An error occurred while using the Unstructured API: {e}")
        except Exception as e:
            print(f"An error occurred while using the Unstructured API: {e}")

    def TableExtractionStrategy(self, filepath) -> List:
        """
        Load the documents using the a PDF Loader that supports table extraction. This strategy is used for documents that contain tables.
        Right now I will try using camelot-py to extract tables from the documents. There is also the option use tablua-py
        Eventually unstructured should be able to handle all of this. (text, math formulas and tables)

        Notes:
          Camelot throws an error because it uses PDFReader internally and it's deprecated. I will try to use tabula-py instead or read docs to see if there is a way to use camelot-py.
          I think pdfplumber can work well here as well

        Returns:
          To be determined
        """

    def OpenAIVisionStrategy(self, file_path: str):
        """
        Load the documents using the OpenAI Vision API. This strategy is used for documents that contain text and mathematical formulas like LaTex.
        I'm unsure if this strategy also works with tables.

        Returns:
          To be determined
        """
        pass

    def ClaudeUtility(self, response_obj: Message):  # To be determined
        """
        Utility function to use the Claude AI Vision Strategy.
        """
        # Extract the text from the response object
        message_text = response_obj.content[0].text

        # Unescape Latex Formulas - For JSON it appraenlty needs it
        # message_text = message_text.replace("\\\\", "\\")

        # Parse the unescaped string as JSON
        json_data = json.loads(message_text)

        # Extract the text from the JSON data
        extracted_text = json_data["page_content"]
        page = json_data["page"]
        source = json_data["source"]

        # Create a new dict
        extracted_text_dict = {
            "page_content": extracted_text,
            "page": page,
            "source": source,
        }

        # Return the extracted text
        filename = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + ".json"
        with open(f"data/claude_output/formatted_page/{filename}", "w") as f:
            json.dump(extracted_text_dict, f, indent=2)

        print("JSON data extracted and dumped successfully.")

    def ClaudeAIVisionStrategy(self, file_path: str):
        """
        Load the documents using the Claude AI Vision API. This strategy is used for documents that contain text and mathematical formulas like LaTex.
        I'm unsure if this strategy also works with tables.

        Note
          Works well with text and math formulas. Need to try it with tables (21.03.2024)

        Returns:
          Formatted JSON that can be loaded into a json file
        """
        client = anthropic.Anthropic()
        try:
            pages = convert_from_path(
                file_path, first_page=1, last_page=1, thread_count=2
            )
            page = pages[0]
            page.save("out.jpg", "JPEG")
            buffered = BytesIO()
            page.save(buffered, format="JPEG")
            image_data = base64.b64encode(buffered.getvalue()).decode("utf-8")
        except Exception as e:
            print(f"An error occurred while converting the PDF to an image: {e}")

        try:
            # API Call - Question: How many pages at once. At what point do I need to do multiple calls?
            message = client.messages.create(
                model=config.LLM_Config.ClaudeAI_Chat_Model,
                max_tokens=1024,
                temperature=0.2,
                system=config.LLM_Config.Claude_system_prompt,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/jpeg",
                                    "data": image_data,
                                },
                            },
                            {
                                "type": "text",
                                "text": "Please extract the text, mathematical formulas, and tables from this image.",
                            },
                        ],
                    }
                ],
            )

            self.ClaudeUtility(message)
            filename = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + ".json"
            print("Usage: ", message.usage)
            with open(f"data/claude_output/{filename}", "w") as f:
                json.dump(message.model_dump(), f, indent=2)
        except APIError as e:
            print(f"An API error occurred while using the Claude AI Vision API: {e}")
        except Exception as e:
            print(
                f"An general error occurred while using the Claude AI Vision API: {e}"
            )

        # Load the pdf and convert to base64 img

    def nougatCloudStrategy(self, file_path: str):
        """
        Load the documents using the Nougat API and running it in the cloud.
        This is strategy works with very complex and unstructured documents but is a ML model that can't be run locally without a lot of resources.

        Returns:
          To be determined
        """
        pass

    # Utils
    def store_extracted_text(self, extracted_text, filepath: str, folder: str) -> None:
        """
        Utility function to store the extracted text to a file.
        Store the extracted text to a file. \n
        Parameters:
          extracted_text (str): The extracted text.
        Returns:
          None
        """
        output_dir = os.path.join(self.folder_path, folder)
        os.makedirs(output_dir, exist_ok=True)
        # Create a unique filename for each extracted text
        base_name = os.path.basename(filepath)
        output_filename = os.path.join(output_dir, f"{base_name}.txt")
        # Write the extracted text to the output file
        text_to_write = [doc.page_content for doc in extracted_text]
        with open(output_filename, "w", encoding="utf-8") as file:
            file.write("\n".join(text_to_write))

    def load_docs_from_json(self, file_path):
        """
        Utility function to load the documents from a JSON file.
        Load the documents from a JSON file.

        Parameters:
          file_path (str): The path to the JSON file.

        Returns:
          List[Document]: The loaded documents.
        """
        documents = []
        with open(file_path, "r") as f:
            data = json.load(f)

        for doc in data:
            document = Document(
                page_content=doc["page_content"],
                metadata=doc["metadata"],
                type=doc["type"],
            )
            documents.append(document)
        print("Documents loaded from JSON.")
        return documents

    # For testing purposes
    def load_one_document(self, file_path: str) -> List:
        try:
            extracted_doc = PyMuPDFLoader(file_path).load()
            print(extracted_doc)

            # Save the extracted text to a JSON file for viewing
            documents_dict = [doc.__dict__ for doc in extracted_doc]

            with open("output.json", "w") as f:
                json.dump(documents_dict, f, indent=2)

            self.documents.append(extracted_doc)
            self.store_extracted_text(extracted_doc, file_path, "extracted_text")
        except Exception as e:
            print(f"Error reading {file_path} with Error: {e}")
        return self.documents


# Example usage: that's fine
ingestion = DataIngestion("./data/simple_pdfs-json_for_trial_1")
# ingestion.UnstructuredStrategy("data/raw_pdfs/2_Appraisal Methods.pdf")
ingestion.ClaudeAIVisionStrategy(
    "data/raw_pdfs/6_Formula_Real Estate Appraisal Formulas.pdf"
)
