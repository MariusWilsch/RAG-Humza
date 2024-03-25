from langchain_community.vectorstores import chroma
from langchain_openai import OpenAIEmbeddings
from langchain.schema.document import Document
from openai import OpenAI
from typing import List, Tuple
from pprint import pprint
import json

# Constants - Move later to app.config.yaml
embedding_model = "text-embedding-3-small"
k = 3
llm_engine = "gpt-3.5-turbo"

chromeDB = chroma.Chroma(
    persist_directory="data/vectordb",
    embedding_function=OpenAIEmbeddings(model=embedding_model),
)


def document_to_dic(doc: Document):
    return {
        "page_content": doc.page_content,
        "metadata": doc.metadata,
        "type": doc.type,
    }


def raq_in_terminal() -> None:
    while True:
        userPrompt = input("\n\nEnter your question or press 'q' to exit: ")
        if userPrompt.lower() == "q":
            break
        userPrompt = "# user new question:\n" + userPrompt
        result = chromeDB.similarity_search(userPrompt, k=3)
        # result_as_dict = [document_to_dic(x) for x in result]
        # with open("resultForViewing.json", "w") as f:
        #     json.dump(result_as_dict, f, indent=2)
        convert_to_str: List[Tuple] = [str(x.page_content) + "\n\n" for x in result]
        retrived_docs_str = "# Retrieved content:\n\n" + str(convert_to_str)
        prompt = retrived_docs_str + "\n\n" + userPrompt
        completion = OpenAI.chat.completions.create(
            model=llm_engine,
            messages=[
                {"role": "system", "content": "system"},
                {"role": "user", "content": prompt},
            ],
        )
        pprint(completion.choices[0].message.content)
        break


raq_in_terminal()
