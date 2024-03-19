import os, json
from typing import List
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import chroma

# Gloabls - Later convert that in to app.config.yaml
chunk_size = 500
chunk_overlap = 100
embedding_model = "text-embedding-3-small"


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
        self.folder_path = folder_path
        self.documents = []

    def chunk_documents(self, documents: List, chunk_size: int) -> List:
        """
        Chunk the documents into smaller pieces.

        Parameters:
            documents (List): The documents to chunk.
            chunk_size (int): The size of the chunks.

        Returns:
            List: The chunked documents.
        """
        print("Chunking documents...")
        chunked_docs = self.text_splitter.split(documents)
        print("Num of chunks:", len(chunked_docs), "\n")

    def prep_and_save_vectordb(self, jsonDirectory, pdfDirectory) -> None:
        """
        Embed the documents and save the VectorDB.

        Parameters:
            documents (List): The chunked documents to embed.

        Returns:
          Chroma: The created VectorDB.
        """
        docs = self.load_docs_from_json()
        docs.append(self.BasicTextStrategy())
        chunked_docs = self.chunk_documents(docs)
        print("Embedding documents...")
        chromaCli = chroma.Chroma()
        vectordb = chromaCli.from_documents(
            documents=chunked_docs,
            embedding=self.embedding_engine,
            persist_directory="data/vectordb",
        )
        print("VectorDB created and saved.")
        print("Num of vectors:", vectordb._collection.count(), "\n")
        return vectordb

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

    def BasicTextStrategy(self) -> List:
        """
        Load the documents using the a basic PDF Loader, i.e PyMuPDF. This strategy is used for documents that are mostly text.
        It does not work well with table and mathematical formulas like LaTex.

        Returns:
          List[Doucment]: A list of loaded documents with metadata.
        """
        docs_cnt = 0
        for file in os.listdir(self.folder_path):
            if not file.endswith(".pdf"):
                continue
            filepath = os.path.join(self.folder_path, file)
            try:
                # for testing purposes - use this in the final version # self.documents.append(PyMuPDFLoader(filepath).load())
                extracted_doc = PyMuPDFLoader(filepath).load()

                self.documents.append(extracted_doc)
                # Save the extracted text (page_content=[...]) into a txt file for viewing
                self.store_extracted_text(
                    extracted_doc, filepath, "extracted_text_for_viewing"
                )
                # Save the extracted text to a JSON file for viewing
                # Not implemented yet
                docs_cnt += 1
            except Exception as e:
                print(f"Error reading {file} with Error: {e}")
        print("Number of loaded documents:", docs_cnt)
        return self.documents

    def TableExtractionStrategy(self, filepath) -> List:
        """
        Load the documents using the a PDF Loader that supports table extraction. This strategy is used for documents that contain tables.
        Right now I will try using camelot-py to extract tables from the documents. There is also the option use tablua-py
        Eventually unstructured should be able to handle all of this. (text, math formulas and tables)

        Notes:
          Camelot throws an error because it uses PDFReader internally and it's deprecated. I will try to use tabula-py instead or read docs to see if there is a way to use camelot-py.

        Returns:
          To be determined
        """

        # Extract tables from pdfs
        # tables = camelot.read_pdf(filepath, flavor="stream", pages="all")

        # Visualize the tables
        # tables.export(
        #     "output.csv", f="csv", compress=True
        # )  # to export the tables to a csv file
        # camelot.plot(tables[0], kind="grid").show()
        # for i, table in enumerate(tables):
        #     print(f"Table {i}:")
        #     print(table.df)

    def OpenAIVisionStrategy(self, file_path: str):
        """
        Load the documents using the OpenAI Vision API. This strategy is used for documents that contain text and mathematical formulas like LaTex.
        I'm unsure if this strategy also works with tables.

        Returns:
          To be determined
        """
        pass

    def ClaudeAIVisionStrategy(self, file_path: str):
        """
        Load the documents using the Claude AI Vision API. This strategy is used for documents that contain text and mathematical formulas like LaTex.
        I'm unsure if this strategy also works with tables.

        Returns:
          To be determined
        """
        pass

    def UnstructuredStrategy(self, file_path: str):
        """
        Load the documents using the Unstructured API. This strategy is used for documents that contain text, mathematical formulas like LaTex and tables.
        According to my research this API is made for complex documents and also offers additional features like cleaning

        Returns:
          To be determined
        """
        pass

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
          dict: The loaded documents.
        """
        documents = []
        with open(file_path, "r") as f:
            data = json.load(f)

        for doc in data:
            document = {
                "page_content": doc["page_content"],
                "metadata": doc["metadata"],
                "type": doc["type"],
            }
            documents.append(document)
        print("Documents loaded from JSON.")
        print(documents)
        return documents


# Example usage:
ingestion = DataIngestion("./data")
ingestion.load_docs_from_json(
    "data/processed/5_Formula_The Mathematics of Real Estate.pdf.json"
)
