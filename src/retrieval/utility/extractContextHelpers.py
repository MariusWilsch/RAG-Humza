from pprint import pprint
from langchain.schema.document import Document
from typing import Tuple


def extract_page_context(docs: Document):
    page_ctx = []
    pprint(docs, indent=2)
    try:
        for doc in docs:
            source: str = doc.metadata.get("filename") or doc.metadata.get("source")
            page_number: str = doc.metadata.get("page_number") or doc.metadata.get(
                "page"
            )
            if page_number is None:
                raise ValueError(
                    "Both 'page_number' and 'page' are missing from metadata"
                )
            page_ctx.append((doc.page_content, source, page_number))
    except Exception as e:
        print(f"An error occurred while extracting context: {e}")
    return page_ctx


def set_most_similar_pdf(pdf_metadata: Tuple):
    # Extract source and page_number from the tuple
    source = pdf_metadata[1]
    page_number = pdf_metadata[2]
    print(f"Most similar PDF: {source}")
    return {"file_name": source, "page": page_number}


def format_and_simplify_context(page_ctx):
    formatted_ctx = [
        f"In Document {source} in page {page}:\n\n{content}"
        for content, source, page in page_ctx
    ]
    formatted_ctx = "\n\n".join(formatted_ctx)
    simplified_page_ctx = [(source, page) for _, source, page in page_ctx]
    return formatted_ctx, simplified_page_ctx
