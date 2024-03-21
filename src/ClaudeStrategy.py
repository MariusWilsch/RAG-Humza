import base64, os, yaml
from anthropic import APIError, Anthropic
from anthropic.resources.messages import Message
from pdf2image import convert_from_path
from io import BytesIO
from dataclasses import dataclass


@dataclass
class LLM_CONFIG:
    """
    This class is used to store the configuration for the LLM model
    """

    CLAUDE_MODEL: str
    CLAUDE_SYSTEM_PROMPT: str


with open("config/config.yml", "r") as file:
    data = yaml.safe_load(file)

config = LLM_CONFIG(**data["LLM_Config"])

client = Anthropic()


def ClaudeVisionPDFParser(file_path: str):
    """
    This function is used to parse the PDF file and extract the text from it
    """
    # Temp variable to store the extracted data
    extracted_data = []
    try:
        # Extract all pages using pdf2image
        pages = convert_from_path(file_path, thread_count=4)
    except Exception as e:
        print("Error while extracting pages from PDF using pdf2image: ", e)

    for page_num, page in enumerate(pages, start=1):
        # Convert the page to an base64 encoded image
        image_data = convert2base64(page)

    # Convert the page to an base64 encoded image


def convert2base64(page):
    """
    This function is used to convert the page to a base64 encoded image
    """
    # Convert the page to a base64 encoded image
    buffered = BytesIO()
    page.save(buffered, format="JPEG")
    image_data = base64.b64encode(buffered.getvalue()).decode("utf-8")
    return image_data


def callClaude(image_data):
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

    message = client.messages.create(
        model=config.CLAUDE_MODEL,
        max_tokens=1024,
        temperature=0.2,
        system=config.CLAUDE_SYSTEM_PROMPT,
        messages=messages,
    )
