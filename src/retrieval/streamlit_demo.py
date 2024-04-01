import sys, re
import streamlit as st

sys.path.append("src")
from utility.load_config import AppConfig, load_config
from retrieval.process_query import process_query
from retrieval.utility.init_session_state import initialize_session_state
from retrieval.utility.process_uploaded_file import process_uploaded_file
from retrieval.utility.download_file import process_download


# Load configuration
config: AppConfig = load_config()

# Globals
CUR_SYSTEM_PROMPT = config.OPENAI.SYSTEM_PROMPT_LAW
CUR_PERSIST_DIR = "data/RAG_LAW/store"

# UI
st.title("Document Assistant")
st.subheader("Ask me a question about your documents")
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

# Display messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if message["role"] == "user":
            st.markdown(message["content"])
        elif message["role"] == "assistant":
            st.markdown(message["content"])
    if message["role"] == "assistant":
        with st.expander("Annotations"):
            st.write(message["annotations"])

# Main chat loop
if prompt := st.chat_input("Ask me a question about your documents"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    # Display user prompt
    with st.chat_message("user"):
        st.markdown(prompt)
    # Show a spinner
    with st.spinner("Thinking..."):
        # Process the user prompt
        llm_response, annotations, ctx = process_query(
            prompt,
            CUR_SYSTEM_PROMPT,
            config.OPENAI.CHAT_MODEL,
            config.CHROMA.K_RESULTS,
            st.session_state,
        )
        if llm_response is None:
            st.error("Error while processing your request", icon="🚨")
        else:
            # Display response
            with st.chat_message("assistant"):
                st.markdown(llm_response)
            with st.expander("Annotations"):
                st.write(annotations)
            if "mostSimilarPDF" in st.session_state:
                pdf_data = process_download(
                    st.session_state.mostSimilarPDF, CUR_PERSIST_DIR
                )
                if pdf_data:
                    st.sidebar.download_button(
                        label="Download most similar PDF",
                        data=pdf_data,
                        file_name=st.session_state.mostSimilarPDF,
                        mime="application/pdf",
                    )
            with st.sidebar:
                st.title("Retrieved Context")
                with st.expander("Show Context"):
                    formatted_ctx = re.sub(r"(In Document\[^:\]+:)", r"\n\1\n", ctx)
                    st.write(formatted_ctx.replace("\n\n", "\n"))
                    st.session_state.messages.append(
                        {
                            "role": "assistant",
                            "content": llm_response,
                            "annotations": annotations,
                        }
                    )
