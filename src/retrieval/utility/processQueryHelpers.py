import json, os, datetime


def create_prompt(formatted_ctx, userPrompt, previous_prompts_str):
    prompt = (
        "Retrieved context:\n\n"
        + formatted_ctx
        + "\n\n"
        + "Previous prompts and responses:\n\n"
        + previous_prompts_str
        + "New user prompt:\n"
        + userPrompt
        + "\n\n"
    )
    return prompt


def request_chat_completions(
    prompt,
    client,
    chat_model,
    system_message,
):
    return client.chat.completions.create(
        model=chat_model,
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": prompt},
        ],
        temperature=0.5,
    )


def generate_annotations(page_ctx):
    return " and ".join(
        f"Found in source {source} in page {page}" for source, page in page_ctx
    )


def save_json_data(data):
    os.makedirs("manual_verification", exist_ok=True)
    file_name = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    with open(f"manual_verification/{file_name}.json", "w") as f:
        json.dump(data, f, indent=2)
