from langchain.text_splitter import RecursiveCharacterTextSplitter

# Import necessary libraries
from retrieval.utility.upload_file import save_as_json, save_file_to_disk
from ingestion.load_json_into_vectordb import create_vector_db, JSONLoaderType
from extrating.PyPDFStratgy import pyMuPDFLoader


def process_uploaded_file(uploaded_file, st, CUR_PERSIST_DIR):
    if uploaded_file is None:
        st.error(
            "Please upload a file before pressing the 'Process uploaded file' button."
        )
        return

    if uploaded_file.name in st.session_state.processed_file:
        st.error("This file has already been processed.")
        return

    with st.status("Extracting text from PDF...", state="running") as status:
        path = save_file_to_disk(uploaded_file)
        docs = pyMuPDFLoader(path=path)
        save_as_json(docs, uploaded_file.name)
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=250, chunk_overlap=30
        )
        chunked_docs = text_splitter.split_documents(docs)
        status.update(
            label="Adding document to the knowledge base...",
            state="running",
            expanded=False,
        )
        st.write("Text extracted from the PDF file.")
        create_vector_db(chunked_docs, CUR_PERSIST_DIR, JSONLoaderType.PYMUPDF)
        st.write("Document added to the knowledge base.")
        status.update(
            label="Document added to the knowledge base.",
            state="complete",
            expanded=False,
        )

    st.session_state.processed_file.append(uploaded_file.name)
