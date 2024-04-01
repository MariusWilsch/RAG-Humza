from pprint import pprint
from langchain.schema.document import Document


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


def set_most_similar_pdf(docs: Document):
    temp = docs[0].metadata.get("filename") or docs[0].metadata.get("source")
    print(f"Most similar PDF: {temp}")
    return temp


def format_and_simplify_context(page_ctx):
    formatted_ctx = [
        f"In Document {source} in page {page}:\n\n{content}"
        for content, source, page in page_ctx
    ]
    formatted_ctx = "\n\n".join(formatted_ctx)
    simplified_page_ctx = [(source, page) for _, source, page in page_ctx]
    return formatted_ctx, simplified_page_ctx
