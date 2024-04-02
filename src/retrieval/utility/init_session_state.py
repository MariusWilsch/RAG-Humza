from langchain_community.vectorstores import chroma
from langchain_openai import OpenAIEmbeddings
from openai import OpenAI


def initialize_session_state(
    session_state: dict,
    CUR_PERSIST_DIR: str,
    EMBEDDING_MODEL: str,
):
    if "processed_file" not in session_state:
        session_state.processed_file = []

    if "vector_store" not in session_state:
        session_state.vector_store = chroma.Chroma(
            persist_directory=CUR_PERSIST_DIR,
            embedding_function=OpenAIEmbeddings(
                model=EMBEDDING_MODEL,
            ),
        )

    if "openai_cli" not in session_state:
        session_state.openai_cli = OpenAI()

    if "messages" not in session_state:
        session_state.messages = []

    if "mostSimilarPDF" not in session_state:
        session_state.mostSimilarPDF = {"file_name": None, "page": None}
