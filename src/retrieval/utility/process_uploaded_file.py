from retrieval.utility.upload_file import save_file_to_disk
from ingestion.load_json_into_vectordb import create_vector_db, JSONLoaderType
from extrating.UnstructuredStrategy import UnstructuredStrategy, PDFType


def process_uploaded_file(uploaded_file, st, CUR_PERSIST_DIR):
    if uploaded_file is None:
        st.error(
            "Please upload a file before pressing the 'Process uploaded file' button."
        )
        return

    if uploaded_file.name in st.session_state.processed_file:
        st.error("This file has already been processed.")
        return

    with st.status("Extracting text from PDF...", state="running"):
        save_file_to_disk(uploaded_file.read(), CUR_PERSIST_DIR, uploaded_file.name)
        uploaded_file.seek(0)
        UnstructuredStrategy(uploaded_file, PDFType.UPLOAD)
        st.write("Text extracted from the PDF file.")

    with st.status("Adding the document to the knowledge base...", state="running"):
        create_vector_db(
            "unstructured/uploaded", CUR_PERSIST_DIR, JSONLoaderType.UNSTRUCTURED
        )
        st.write("Document added to the knowledge base.")

    st.session_state.processed_file.append(uploaded_file.name)
