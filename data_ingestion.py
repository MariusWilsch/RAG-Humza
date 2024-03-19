import os, json
from typing import List
from langchain_community.document_loaders import (
    PyMuPDFLoader,
    PyPDFLoader,
    MathpixPDFLoader,
)
from PIL import Image
from pix2tex.cli import LatexOCR
from pdf2image import convert_from_path


# Terminologies in Real Esate Appraisal - Comments
# Header cou


class DataIngestion:
    """Class to read out text, formulas and possibilty text from pdfs and word documents. It embdes it and then uploads it to a vector database."""

    def __init__(self, folder_path: str) -> None:
        """
        Initialize the DataIngestion instance.

        Parameters:
            folder_path (str): The directory containing the documents.
            document (List[str]): A list of loaded documents.
        """

        self.folder_path = folder_path
        self.documents = []

    # For testing purposes
    def load_one_document(self, file_path: str) -> List:
        try:
            extracted_doc = PyMuPDFLoader(file_path).load()
            # extracted_doc = PyPDFLoader(file_path).load_and_split()
            # extracted_doc_math = MathpixPDFLoader(file_path).load()
            print(extracted_doc)

            documents_dict = [doc.__dict__ for doc in extracted_doc]

            with open("output.json", "w") as f:
                json.dump(documents_dict, f, indent=2)

            # self.documents.append(extracted_doc)
            # self.store_extracted_text(extracted_doc_math, file_path, "mathpix_text")
        except Exception as e:
            print(f"Error reading {file_path} with Error: {e}")
        return self.documents

    def load_all_documents(self) -> List:
        docs_cnt = 0
        for file in os.listdir(self.folder_path):
            if not file.endswith(".pdf"):
                continue
            filepath = os.path.join(self.folder_path, file)
            try:
                # for testing purposes - use this in the final version # self.documents.append(PyMuPDFLoader(filepath).load())
                extracted_doc = PyMuPDFLoader(filepath).load()
                # print(extracted_doc[:100])
                self.documents.append(extracted_doc)
                self.store_extracted_text(extracted_doc, filepath, "extracted_text")
                docs_cnt += 1
            except Exception as e:
                print(f"Error reading {file} with Error: {e}")
        print("Number of loaded documents:", docs_cnt)
        return self.documents

    def store_extracted_text(self, extracted_text, filepath: str, folder: str) -> None:
        """
        Store the extracted text to a file.
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

    def get_latex_predictions_from_pdf(self) -> list:
        # Convert the PDF to a list of images
        images = convert_from_path("data/6_Formula_Real Estate Appraisal Formulas.pdf")
        model = LatexOCR()

        # Initialize an empty list to store the LaTeX predictions
        latex_predictions = []

        # Loop over each image
        for image in images:
            # Convert the image to a string
            latex_predictions.append(model.model(image))

        print(latex_predictions)


# Example usage:
ingestion = DataIngestion("./data")
ingestion.load_one_document("data/6_Formula_Real Estate Appraisal Formulas.pdf")
# ingestion.get_latex_predictions_from_pdf()
# ingestion.load_all_documents()


# def __load_all_documents(self) -> None:
#     for filename in os.listdir(self.folder_path):
#         if not filename.endswith(".pdf"):
#             continue
#         filepath = os.path.join(self.folder_path, filename)
#         try:
#             self.documents.append(self.__extract_text(filepath))
#         except Exception as e:
#             print(f"Error reading {filename} with Error: {e}")

# def __extract_text(self, file_path: str) -> str:
#     """
#     Extract text from the loaded documents.

#     Returns:
#       str: Extracted text.
#     """
#     text = ""
#     try:
#         with fitz.open(file_path) as doc:
#             for page in doc:
#                 text += page.get_text("text")
#     except Exception as e:
#         print(f"Error extracting text from {file_path}: {e}")
#     return text
