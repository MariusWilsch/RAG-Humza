from pprint import pprint
import sys
import streamlit as st
from dotenv import load_dotenv
from streamlit_pdf_viewer import pdf_viewer

sys.path.append("src")
from utility.load_config import AppConfig, load_config
from retrieval.process_query import process_query
from retrieval.utility.init_session_state import initialize_session_state
from retrieval.utility.process_uploaded_file import process_uploaded_file
from retrieval.display_st import (
    display_assistant_response,
    display_retrieved_context,
    display_download_button,
)

# Load environment variables
load_dotenv()


# Load configuration
config: AppConfig = load_config()

# Globals
CUR_SYSTEM_PROMPT = config.OPENAI.SYSTEM_PROMPT_LAW
CUR_PERSIST_DIR = "data/RAG_LAW/store"

# UI
st.title("Document Assistant")
# Sidebar


with st.sidebar:
    st.title("Instructions")
    with st.expander("How to use"):
        st.markdown(
            "1. Ask a question about your documents\n"
            "2. The assistant will retrieve relevant context from your documents and provide an answer.\n"
            "3. The assistant will also provide annotations to show where the information was found.\n"
            "4. The retrieved context will be displayed on the right sidebar."
        )

    st.title("Upload a PDF file")
    uploaded_file = st.file_uploader(
        "Upload a PDF file", type=["pdf"], label_visibility="collapsed"
    )
    if st.button("Process uploaded file"):
        process_uploaded_file(
            uploaded_file,
            st,
            CUR_PERSIST_DIR,
        )


# Call the function to initialize session state
initialize_session_state(
    st.session_state, CUR_PERSIST_DIR, config.OPENAI.EMBEDDING_MODEL
)


# Create tabs
tab1, tab2 = st.tabs(["Chat", "PDF"])
with tab1:
    messages_container = st.container(height=450)
    # Display messages
    for message in st.session_state.messages:
        with messages_container.chat_message(message["role"]):
            if message["role"] == "user":
                st.markdown(message["content"])
            elif message["role"] == "assistant":
                st.markdown(message["content"])
        if message["role"] == "assistant":
            with messages_container.expander("Annotations"):
                st.write(message["annotations"])

    # Main chat loop
    if prompt := st.chat_input("Ask me a question about your documents"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        messages_container.chat_message("user").markdown(prompt)

        with messages_container:
            with st.spinner("Thinking..."):
                llm_response, annotations, formatted_ctx = process_query(
                    prompt,
                    CUR_SYSTEM_PROMPT,
                    config.OPENAI.CHAT_MODEL,
                    config.CHROMA.K_RESULTS,
                    st.session_state,
                )

                if llm_response is None:
                    st.error("Error while processing your request", icon="🚨")
                else:
                    display_assistant_response(
                        messages_container, llm_response, annotations
                    )
                    display_download_button(st)
                    display_retrieved_context(st, formatted_ctx)

                    st.session_state.messages.append(
                        {
                            "role": "assistant",
                            "content": llm_response,
                            "annotations": annotations,
                        }
                    )


with tab2:
    # Display PDF in the second tab when the user presses a button
    pdf_dict = st.session_state.mostSimilarPDF
    pprint(pdf_dict)
    if filename := pdf_dict.get("file_name"):
        with open(filename, "rb") as f:
            pdf_data = f.read()
        pdf_viewer(
            pdf_data,
            width=800,
            height=600,
            pages_to_render=[pdf_dict.get("page") + 1],
            annotation_outline_size=2,
        )
