import re, streamlit
from retrieval.utility.download_file import process_download


def display_assistant_response(messages_container, llm_response, annotations):
    messages_container.chat_message("assistant").markdown(llm_response)
    messages_container.expander("Annotations").write(annotations)


def display_retrieved_context(st: streamlit, ctx):
    with st.sidebar:
        st.title("Retrieved Context")
        with st.expander("Show Context"):
            formatted_ctx = re.sub(r"(In Document\\\[^:\\\]+:)", r"\\n\\1\\n", ctx)
            st.write(formatted_ctx.replace("\\n\\n", "\\n"))


def display_download_button(st: streamlit):
    if "mostSimilarPDF" in st.session_state:
        file_name = st.session_state.mostSimilarPDF.get("file_name", "")
        if file_name == "":
            st.error("Error: No file name found for download")
            return
        pdf_data = process_download(file_name)
        if pdf_data:
            st.sidebar.download_button(
                label="Download most similar PDF",
                data=pdf_data,
                file_name=file_name,
                mime="application/pdf",
            )
