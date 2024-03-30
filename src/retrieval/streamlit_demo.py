import json, datetime, sys, traceback, os, re

sys.path.append("src")
import streamlit as st
from openai import OpenAI
from pprint import pprint
from utility.load_config import AppConfig, load_config
from langchain_community.vectorstores import chroma
from langchain.schema.document import Document
from langchain_openai import OpenAIEmbeddings
from ingestion.load_json_into_vectordb import create_vector_db, JSONLoaderType
from extrating.UnstructuredStrategy import UnstructuredStrategy, PDFType
import os


# Load configuration
config: AppConfig = load_config()

# Globals
CUR_SYSTEM_PROMPT = config.OPENAI.SYSTEM_PROMPT_LAW
CUR_PERSIST_DIR = "data/RAG_LAW/vectordb"


# UI
st.title("Document Assistant")
st.subheader("Ask me a question about your documents")
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
    if uploaded_file := st.file_uploader(
        "Upload a PDF file", type=["pdf"], label_visibility="collapsed"
    ):
        with st.status("Extracting text from PDF...", state="running") as status:
            UnstructuredStrategy(uploaded_file, PDFType.UPLOAD)
            st.write("Text extracted from the PDF file.")
            status.update(
                label="Adding the document to the knowledge base...", state="running"
            )
            create_vector_db(
                "unstructured/uploaded", CUR_PERSIST_DIR, JSONLoaderType.UNSTRUCTURED
            )
            st.write("Document added to the knowledge base.")
            status.update(
                label="Document added to the knowledge base.", state="complete"
            )

if "vector_store" not in st.session_state:
    st.session_state.vector_store = chroma.Chroma(
        persist_directory=CUR_PERSIST_DIR,
        embedding_function=OpenAIEmbeddings(model=config.OPENAI.OPENAI_EMBEDDING_MODEL),
    )

if "openai_cli" not in st.session_state:
    st.session_state.openai_cli = OpenAI()

if "messages" not in st.session_state:
    st.session_state.messages = []


# Helper functions


def extractContextFromVectorStore(document: Document):
    # Extract the context from the vector store
    page_ctx = []
    pprint(document, indent=2)
    try:
        for doc in document:
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
    # Create a list of formatted context
    formatted_ctx = [
        f"In Document {source} in page {page}:\n\n{content}"
        for content, source, page in page_ctx
    ]
    # Join the formatted context
    formatted_ctx = "\n\n".join(formatted_ctx)
    page_ctx = [(source, page) for _, source, page in page_ctx]
    return formatted_ctx, page_ctx


def process_query(userPrompt):
    print(f"User prompt: {userPrompt}")
    try:
        # Do similarity search with the user prompt
        result = st.session_state.vector_store.similarity_search(
            userPrompt, k=config.CHROMA.K_RESULTS
        )
        # Manipulate the result of the similarity search
        formatted_ctx, page_ctx = extractContextFromVectorStore(result)
        # Append the result to the user prompt
        prompt = (
            "Retrieved context:\n\n"
            + formatted_ctx
            + "\n\n"
            + "New user question: "
            + userPrompt
            + "\n\n"
        )
        # Request chat completions from the model
        res = st.session_state.openai_cli.chat.completions.create(
            model=config.OPENAI.OPENAI_CHAT_MODEL,
            messages=[
                {"role": "system", "content": CUR_SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            temperature=0.5,
        )

        # Return the result of the chat completions
        # llm_response = res.choices[0].message.content.replace("\\\\", "\\")
        llm_response = res.choices[0].message.content
        annotations = " and ".join(
            f"Found in source {source} in page {page}" for source, page in page_ctx
        )
        # Create a json for manual inspection
        data = {"prompt": prompt, "llm_response": llm_response}

        # Generate a unique file name using date and time
        file_name = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

        os.makedirs("manual_verification", exist_ok=True)
        with open(f"manual_verification/{file_name}.json", "w") as f:
            json.dump(data, f, indent=2)
        return llm_response, annotations, formatted_ctx
    except Exception as e:
        print(f"An error occurred in process_query: {e}")
        traceback.print_exc()
        return None, None, None


for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if message["role"] == "user":
            st.markdown(message["content"])
        elif message["role"] == "assistant":
            st.markdown(message["content"])
    if message["role"] == "assistant":
        with st.expander("Annotations"):
            st.write(message["annotations"])

if prompt := st.chat_input("Ask me a question about your documents"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    # Display user prompt
    with st.chat_message("user"):
        st.markdown(prompt)
    # Show a spinner
    with st.spinner("Thinking..."):
        # Process the user prompt
        llm_response, annotations, ctx = process_query(prompt)
        if llm_response is None:
            st.error("Error while processing your request", icon="🚨")
        else:
            # Display response
            with st.chat_message("assistant"):
                st.markdown(llm_response)
            with st.expander("Annotations"):
                st.write(annotations)
            with st.sidebar:
                st.title("Retrieved Context")
                formatted_ctx = re.sub(r"(In Document\[^:\]+:)", r"\n\1\n", ctx)
                st.write(formatted_ctx.replace("\n\n", "\n"))
            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": llm_response,
                    "annotations": annotations,
                }
            )
