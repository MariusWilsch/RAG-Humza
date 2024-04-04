import traceback
from langchain.schema.document import Document
from utility.load_config import AppConfig
from langchain_community.vectorstores import chroma

from retrieval.utility.extractContextHelpers import (
    extract_page_context,
    set_most_similar_pdf,
    format_and_simplify_context,
)

from retrieval.utility.processQueryHelpers import (
    create_prompt,
    request_chat_completions,
    generate_annotations,
    save_json_data,
)


def extractContextFromVectorStore(
    document: Document,
    session_state: dict,
):
    page_ctx = extract_page_context(document)
    session_state.mostSimilarPDF = set_most_similar_pdf(page_ctx[0])
    formatted_ctx, page_ctx = format_and_simplify_context(page_ctx)
    return formatted_ctx, page_ctx

def generate_previous_prompts_string(session_state):
    previous_prompts = session_state.messages[-10:]
    previous_prompts_str = ""
    for i in range(0, len(previous_prompts), 2):
        if i + 1 < len(previous_prompts):
            previous_prompts_str += f"Previous prompt {i // 2 + 1}:\n"
            previous_prompts_str += previous_prompts[i]["content"] + "\n\n"
            previous_prompts_str += f"Previous response {i // 2 + 1}:\n"
            previous_prompts_str += previous_prompts[i + 1]["content"] + "\n\n"
    return previous_prompts_str

def process_query(
    userPrompt: str,
    CUR_SYSTEM_PROMPT: str,
    CHAT_MODEL: str,
    k: int,
    session_state: dict,
):
    print(f"User prompt: {userPrompt}")
    try:
        result = session_state.vector_store.similarity_search(userPrompt, k=k)
        formatted_ctx, page_ctx = extractContextFromVectorStore(result, session_state)
        previous_prompts_str = generate_previous_prompts_string(session_state)
        prompt = create_prompt(formatted_ctx, userPrompt, previous_prompts_str)
        res = request_chat_completions(
            prompt, session_state.openai_cli, CHAT_MODEL, CUR_SYSTEM_PROMPT,
        )
        llm_response = res.choices[0].message.content
        save_json_data({"prompt": prompt, "llm_response": llm_response})
        return llm_response, generate_annotations(page_ctx), formatted_ctx
    except Exception as e:
        print(f"An error occurred in process_query: {e}")
        traceback.print_exc()
        return None, None, None
