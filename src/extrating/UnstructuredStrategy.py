import json, datetime, os

from enum import Enum
from unstructured_client import UnstructuredClient
from unstructured_client.models import shared, errors
from PyPDF2 import PdfReader, PdfWriter

unstucturedCli = UnstructuredClient(
    api_key_auth="QgQU4SrWFfbgNbgmanPwtzQqEMJJwi",
    server_url="https://veloxforce-91m678wr.api.unstructuredapp.io",
)


class PDFType(Enum):
    """
    If the pdf is a standalone pdf or a pdf that has been split into multiple ranges
    """

    STANDALONE = 1
    SPLIT = 2


# CONSTANTS
MAX_PAGES = 100
PAGES_PER_SPLIT = 50

# Utility Functions


def split_pdf_into_ranges(file_path: str, base_filename: str):

    with open(file_path, "rb") as file:
        reader = PdfReader(file)

    num_pages = len(reader.pages)

    if num_pages < MAX_PAGES:
        print(f"Document {file_path} has less than {MAX_PAGES} pages. No need to split")
        return None

    num_splits = num_pages + PAGES_PER_SPLIT - 1 // PAGES_PER_SPLIT

    for i in range(num_splits):
        # Create a new PDF Writer for each split
        writer = PdfWriter()

        # Determine the start and end page for the split
        start_page = i * PAGES_PER_SPLITe
        end_page = min((i + 1) * PAGES_PER_SPLIT, num_pages)

        # Add the pages to the writer
        for page_num in range(start_page, end_page):
            writer.add_page(reader.pages[page_num])

        # Save the split to a new file
        os.makedirs(f"data/split_pdfs/{base_filename}", exist_ok=True)
        split_file_path = f"data/split_pdfs/{base_filename}/{base_filename}_split_{start_page}_{end_page}.pdf"
        with open(split_file_path, "wb") as file:
            writer.write(file)

        print(f"Split range {start_page} - {end_page} saved to {split_file_path}")


def call_strategy_on_folder(folder_path: str, pdf_type: PDFType):
    """
    Call the UnstructuredStrategy for each file in the folder

    Args:
      folder_path: Path to the folder containing the documents
      PDFType: PDFType : If the pdf is a standalone pdf or a pdf that has been split into multiple ranges
    """
    for file in os.listdir(folder_path):
        UnstructuredStrategy(f"{folder_path}/{file}", pdf_type)


def save_json_data(filename: str, data: list, pdf_type: PDFType):
    if filename.endswith(".pdf"):
        filename = filename[:-4]
    if pdf_type == PDFType.STANDALONE:
        now = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        output_file = f"unstructured/{filename}_{now}.json"
        with open(output_file, "w") as f:
            json.dump(data, f, indent=2)
    else:  # PDFType.SPLIT
        output_file = f"unstructured/{filename}.json"
        if os.path.exists(output_file):
            with open(output_file, "r") as f:
                existing_data = json.load(f)
        else:
            existing_data = []
        existing_data.extend(data)
        with open(output_file, "w") as f:
            json.dump(existing_data, f, indent=2)


# Main Function
def UnstructuredStrategy(file_path: str, pdf_type: PDFType):
    """
    Function explanation
    ====================
    Load the documents using the Unstructured API. This strategy is used for documents that contain text, mathematical formulas like LaTex and tables.
    According to my research this API is made for complex documents and also offers additional features like cleaning

    Notes
    -----
      Did not extraxt the Math Formula, didn't check if it works well with tables (21.03.2024)
      It works well with text and tables. I think this strategy can be used for anything that is not a math formula. (21.03.2024, 4pm)

    Args:
    -----
      file_path: str : Path to the document
      pdf_type: PDFType : If the pdf is a standalone pdf or a pdf that has been split into multiple ranges

    Returns:
    --------
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
    # request = shared.PartitionParameters(
    #     files=files,
    #     strategy="ocr_only",
    #     split_pdf_page=True,
    #     languages=["eng, deu"],
    #     chunking_strategy="by_title",
    #     max_characters="1750",
    #     new_after_n_chars="500",
    #     combine_under_n_chars="500",
    # )
    # Hi_res strategy is for complex documents with tables
    # model names, "chipper" or "yolox" or yolox_quantized
    request = shared.PartitionParameters(
        files=files,
        strategy="hi_res",
        pdf_infer_table_structure=True,
        split_pdf_page=True,
        languages=["eng, deu"],
        chunking_strategy="by_title",
        max_characters="1750",
        new_after_n_chars="500",
        combine_under_n_chars="500",
        hi_res_model_name="yolox",
    )

    try:
        response = unstucturedCli.general.partition(request)
        os.makedirs("unstructured", exist_ok=True)
        # Save the data
        save_json_data(filename, response.elements, pdf_type)
        print(f"Document {file_path} was successfully loaded and chunked")
    except errors.SDKError as e:
        print(f"An error occurred while using the Unstructured API: {e}")
    except Exception as e:
        print(f"An error occurred while using the Unstructured API: {e}")


# Call on multiple files
# call_strategy_on_folder(
#     folder_path="data/Neurohabiltation/above100pages/ilovepdf_split-range",
#     pdf_type=PDFType.STANDALONE,
# )

# Call on a single file
# UnstructuredStrategy(
#     "data/Neurohabiltation/raw_pdfs/5-NeuroRehabilitation-A-Multidisciplinary-Approach.pdf",
#     PDFType.STANDALONE,
# )

# Archived version
# try:
#     response = unstucturedCli.general.partition(request)
#     os.makedirs("unstructured", exist_ok=True)
#     now = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
#     if filename.endswith(".pdf"):
#         filename = filename[:-4]
#     with open(f"unstructured/{filename + now}.json", "w") as f:
#         json.dump(response.elements, f, indent=2)
#     print(f"Document {file_path} was successfully loaded and chunked")
# except errors.SDKError as e:
#     print(f"An error occurred while using the Unstructured API: {e}")
# except Exception as e:
#     print(f"An error occurred while using the Unstructured API: {e}")
