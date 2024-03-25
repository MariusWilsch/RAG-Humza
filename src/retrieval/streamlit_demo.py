import json, datetime, sys, traceback, os, ast

sys.path.append("src")
import streamlit as st
from openai import OpenAI
from pprint import pprint
from utility.load_config import AppConfig, load_config
from langchain_community.vectorstores import chroma
from langchain.schema.document import Document
from langchain_openai import OpenAIEmbeddings


# Load configuration
config: AppConfig = load_config()

# UI
st.title("Document Assistant")
st.subheader("Ask me a question about your documents")

if "vector_store" not in st.session_state:
    st.session_state.vector_store = chroma.Chroma(
        persist_directory="data/Neurohabiltation/try1/vectordb",
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
                {"role": "system", "content": config.OPENAI.SYSTEM_PROMPT_NEURO},
                {"role": "user", "content": prompt},
            ],
            temperature=0.0,
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
        return llm_response, annotations
    except Exception as e:
        print(f"An error occurred in process_query: {e}")
        traceback.print_exc()
        return None, None


for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])


if prompt := st.chat_input("Ask me a question about your documents"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    # Display user prompt
    with st.chat_message("user"):
        st.markdown(prompt)

    # Show a spinner
    with st.spinner("Thinking..."):
        # Process the user prompt
        llm_response, annotations = process_query(prompt)
    if llm_response is None:
        st.error("Error while processing your request", icon="🚨")
    else:  # Display response
        with st.chat_message("assistant"):
            st.markdown(llm_response)
            with st.expander("Annotations"):
                st.write(annotations)

    st.session_state.messages.append({"role": "assistant", "content": llm_response})
