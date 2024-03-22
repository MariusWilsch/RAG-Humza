import base64, os, yaml, json, datetime, time
from anthropic import APIError, Anthropic
from anthropic.resources.messages import Message
from pdf2image import convert_from_path
from pprint import pprint
from io import BytesIO
from dataclasses import dataclass
from fix_busted_json import repair_json


@dataclass
class CLAUDE_CONFIG:
    """
    This class is used to store the configuration for the LLM model
    """

    CLAUDE_MODEL: str
    CLAUDE_SYSTEM_PROMPT: str


with open("config/config.yml", "r") as file:
    data = yaml.safe_load(file)

config = CLAUDE_CONFIG(**data["CLAUDE_CONFIG"])

client = Anthropic()


def ClaudeVisionPDFParser(file_path: str):
    """
    This function is used to parse the PDF file and extract the text from it
    """
    # Temp variable to store the extracted data
    json_data = []
    try:
        # Extract all pages using pdf2image
        pages = convert_from_path(file_path, thread_count=2)
        print(f"Extracted {len(pages)} pages from the PDF")
    except Exception as e:
        print("Error while extracting pages from PDF using pdf2image: ", e)

    for page_num, page in enumerate(pages, start=1):
        # Convert the page to an base64 encoded image
        image_data = convert2base64(page)
        page_content = processMessage(callClaude(image_data), page_num, file_path)
        if page_content is None:
            break  # Stop the loop if the page content is None
        filename = os.path.basename(file_path)
        json_data.append(
            {"page_content": page_content, "page": str(page_num), "source": filename}
        )
        print(f"Processed page {page_num} from {filename}")
        time.sleep(1)  # Sleep for 1 second to avoid rate limiting

    now = "_" + datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    filename = filename + now + ".json"
    with open(f"data/claude_output/{filename}", "w") as f:
        json.dump(json_data, f, indent=2)


def convert2base64(page):
    """
    This function is used to convert the page to a base64 encoded image
    """
    # Convert the page to a base64 encoded image
    buffered = BytesIO()
    page.save(buffered, format="JPEG")
    image_data = base64.b64encode(buffered.getvalue()).decode("utf-8")
    return image_data


def callClaude(image_data) -> Message:
    messages = (
        [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/jpeg",
                            "data": image_data,
                        },
                    },
                    {
                        "type": "text",
                        "text": "Please extract the text, mathematical formulas, and tables from this image.",
                    },
                ],
            }
        ],
    )

    print("Calling Claude...")
    try:
        message = client.messages.create(
            model=config.CLAUDE_MODEL,
            max_tokens=1024,
            temperature=0.2,
            system=config.CLAUDE_SYSTEM_PROMPT,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/jpeg",
                                "data": image_data,
                            },
                        },
                        {
                            "type": "text",
                            "text": "Please extract the text, mathematical formulas, and tables from this image.",
                        },
                    ],
                }
            ],
        )
        print("Claude response: ", message.content[0].text)
        return message
    except APIError as e:
        print("Error while calling Claude: ", e)
        return None


def processMessage(message: Message, page_num: int, source_file: str) -> dict:
    """
    This function is used to process the message and extract the data from it
    """

    try:
        # Convert text to JSON
        message_text = message.content[0].text
        fixed_json = repair_json(message_text)
        json_data = json.loads(fixed_json)
        return json_data["page_content"]
    except Exception as e:
        print(f"Error while processing page {page_num}", e)
        return None


ClaudeVisionPDFParser(
    "data/vectordb/try2/raw_pdf_for_claude_vision/6_Formula_Real Estate Appraisal Formulas.pdf"
)
