from typing import List, Tuple, Dict, Any, Union
from pathlib import Path
from io import BufferedReader, BytesIO
import pdfplumber


def extract_table_and_text(
    path_or_fp: Union[str, Path, BufferedReader, BytesIO],
    pages: Union[List[int], Tuple[int], None] = None,
    debug: bool = False,
):
    with pdfplumber.open(
        path_or_fp,
        pages=pages,
    ) as pdf:
        results = []
        for page_num in pages or range(len(pdf.pages)):
            page = pdf.pages[page_num]
            text = page.extract_text()
            table = page.extract_table()

            if debug:
                im = page.to_image()
                print(f"Page {page_num + 1}:")
                im
                print("Extracted Table:")
                print(table)
                print("Extracted Text:")
                print(text)
                print("=" * 50)

            results.append({"page": page_num + 1, "table": table, "text": text})

    return results


extract_table_and_text(
    "data/raw_pdfs/5_Formula_The Mathematics of Real Estate.pdf",
    debug=True,
)
