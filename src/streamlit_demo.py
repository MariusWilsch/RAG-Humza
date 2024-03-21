import yaml, json, datetime
import streamlit as st
from uuid import uuid4
from pprint import pprint
from openai import OpenAI
from langchain_community.vectorstores import chroma
from langchain.schema.document import Document
from langchain_openai import OpenAIEmbeddings
from dataclasses import dataclass


@dataclass
class LLM_Config:
    system_prompt1: str
    system_prompt2: str
    system_prompt3: str
    OPENAI_Chat_Model: str
    OPENAI_Embedding_Model: str
    Chunk_Size: int
    Chunk_Overlap: int


@dataclass
class Chroma:
    persistDir: str
    k_results: int


@dataclass
class Config:
    LLM_Config: LLM_Config
    Chroma: Chroma


# Get the config
with open("config/config.yml", "r") as f:
    data = yaml.safe_load(f)

config = Config(
    LLM_Config=LLM_Config(**data["LLM_Config"]), Chroma=Chroma(**data["Chroma"])
)

if "vector_store" not in st.session_state:
    st.session_state.vector_store = chroma.Chroma(
        persist_directory=config.Chroma.persistDir,
        embedding_function=OpenAIEmbeddings(
            model=config.LLM_Config.OPENAI_Embedding_Model
        ),
    )

if "openai_cli" not in st.session_state:
    st.session_state.openai_cli = OpenAI()


def extractContextFromVectorStore(document: Document):
    # Extract the context from the vector store
    page_ctx = [
        (
            doc.page_content,
            doc.metadata["source"].replace("./data/simple_pdfs-json_for_trial_1/", ""),
            doc.metadata["page"],
        )
        for doc in document
    ]
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
    try:
        # Do similarity search with the user prompt
        result = st.session_state.vector_store.similarity_search(
            userPrompt, k=config.Chroma.k_results
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
            model=config.LLM_Config.OPENAI_Chat_Model,
            messages=[
                {"role": "system", "content": config.LLM_Config.system_prompt2},
                {"role": "user", "content": prompt},
            ],
        )

        # Return the result of the chat completions
        llm_response = res.choices[0].message.content
        annotations = " and ".join(
            f"Found in source {source} in page {page + 1}" for source, page in page_ctx
        )

        # Fix Latex Formulas
        # llm_response.replace("\frac", "\\frac")

        # Create a json for manual inspection
        data = {"prompt": prompt, "llm_response": llm_response}

        # Generate a unique file name using date and time
        file_name = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

        with open(f"manual_verification/{file_name}.json", "w") as f:
            json.dump(data, f, indent=2)
        return llm_response, annotations
    except Exception as e:
        print(f"An error occurred: {e}")
        return None


# UI
st.title("Document Assistant")
st.subheader("Ask me a question about your documents")

# Init chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history on rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

if prompt := st.chat_input("Ask me a question about your documents"):
    # Display user prompt
    with st.chat_message("user"):
        st.markdown(prompt)

    # Show a spinner
    with st.spinner("Thinking..."):
        # Process the user prompt
        llm_response, annotations = process_query(prompt)

    if llm_response is None:
        st.error("Error while processing your request", icon="🚨")
    else:
        # Display response
        with st.chat_message("assistant"):
            st.markdown(
                f"{llm_response} <br> **Annotations** {annotations}",
                unsafe_allow_html=True,
            )

        # Add response to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.session_state.messages.append({"role": "assistant", "content": llm_response})
