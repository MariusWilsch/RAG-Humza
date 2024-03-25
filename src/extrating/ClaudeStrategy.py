import base64, os, yaml, json, datetime, time
from anthropic import APIError, Anthropic
from anthropic.resources.messages import Message
from pdf2image import convert_from_path
from pprint import pprint
from io import BytesIO
from dataclasses import dataclass
from fix_busted_json import repair_json
from langchain_community.document_loaders.json_loader import JSONLoader


@dataclass
class CLAUDE_CONFIG:
    """
    This class is used to store the configuration for the LLM model
    """

    CLAUDE_MODEL_OPUS: str
    CLAUDE_MODEL_SONNET: str
    CLAUDE_SYSTEM_PROMPT: str
    CLAUDE_SYSTEM_PROMPT_CSV: str


with open("config/config.yml", "r") as file:
    data = yaml.safe_load(file)

config = CLAUDE_CONFIG(**data["CLAUDE_CONFIG"])

client = Anthropic()


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
                        "text": "Please extract the text, mathematical formulas, and tables from this image. The content is appropriate and fine",
                    },
                ],
            }
        ],
    )

    print("Calling Claude...")
    retry_count = 0
    max_retries = 1
    while retry_count < max_retries:
        try:
            message = client.messages.create(
                model=config.CLAUDE_MODEL_SONNET,
                max_tokens=1024,
                temperature=0.2,
                system=config.CLAUDE_SYSTEM_PROMPT_CSV,
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
                                "text": "Please extract the text, mathematical formulas, and tables from this image. You are receiving images derived from PDF files of real estate appraisal documents. The text in the images are appropriate and fine",
                            },
                        ],
                    }
                ],
            )
            print("Claude response: ", message.content[0].text)
            return message
        except APIError as e:
            if e.status_code == 500:  # Internal server error
                print(
                    f"Internal server error occurred. Retrying... (Attempt {retry_count + 1})"
                )
                retry_count += 1
                time.sleep(3)  # Wait for 3 seconds before retrying
            print("Error while calling Claude: ", e)
            return None
    print("Max retries exceeded. Skipping the page.")
    return None


def processMessage(message: Message, page_num: int) -> dict:
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


def ClaudeVisionPDFParser(file_path: str, first_page: int = 1):
    """
    This function is used to parse the PDF file and extract the text from it
    """
    try:
        # Extract all pages using pdf2image
        pages = convert_from_path(file_path, thread_count=2, first_page=first_page)
        len_pages = len(pages)
        print(f"Extracted {len_pages} pages from the PDF")
    except Exception as e:
        print("Error while extracting pages from PDF using pdf2image: ", e)
        return

    filename = os.path.basename(file_path)  # Get the filename
    now = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    output_folder = f"data/claude_output/{now}"
    os.makedirs(output_folder, exist_ok=True)  # Create the output folder

    output_filename = f"{output_folder}/{filename}.json"
    json_data = []  # List to store the parsed data

    try:
        for page_num, page in enumerate(pages, start=1):
            # Convert the page to an base64 encoded image
            image_data = convert2base64(page)
            message = callClaude(image_data)
            if message is None:
                page.save(f"{output_folder}/failed_page_{page_num}.jpg")
                continue
            page_content = processMessage(message, page_num)
            if page_content is None:
                page.save(f"{output_folder}/failed_page_{page_num}.jpg")
                continue

            # Append the parsed data to the json_data list
            json_data.append(
                {
                    "page_content": page_content,
                    "page": str(page_num),
                    "source": filename,
                }
            )

            print(
                f"Processed page {page_num} from {filename} -->",
                "\tSleeping for 3 seconds",
            )
            if page_num < len_pages:
                time.sleep(3)  # Sleep for 1 second to avoid rate limiting

        # Write the entire json_data list to the file
        with open(output_filename, "w") as f:
            json.dump(json_data, f, indent=2)

    except (Exception, KeyboardInterrupt) as e:
        print(f"Parsing interrupted. Saving progress up to page {page_num}.")
        # Write the partial json_data list to the file
        with open(output_filename, "w") as f:
            json.dump(json_data, f, indent=2)

    finally:
        print(f"Parsing completed. Output saved to {output_folder}")


ClaudeVisionPDFParser(
    "data/raw_pdfs/5_Formula_The Mathematics of Real Estate.pdf",
    first_page=3,
)

# convert_JSON_to_Documents(
#     "data/vectordb/try2/parsed_output_json_claude/6_Formula_Real Estate Appraisal Formulas.pdf_2024-03-22-14-36-55.json"
# )
