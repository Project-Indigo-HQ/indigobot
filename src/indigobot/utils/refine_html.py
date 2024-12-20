import json
import os

from bs4 import BeautifulSoup
from langchain.schema import Document

from indigobot.config import RAG_DIR


def load_html_files(folder_path):
    """
    Load all HTML files from a specified directory.

    :param folder_path: Path to the directory containing HTML files.
    :type folder_path: str
    :return: List of file paths to HTML files.
    :rtype: list
    """
    html_files = []
    for filename in os.listdir(folder_path):
        if filename.endswith(".html"):
            file_path = os.path.join(folder_path, filename)
            html_files.append(file_path)
    return html_files


def parse_and_save(file_path):
    """
    Parse an HTML file to extract the title and headers, and save the result as a JSON file.

    :param file_path: Path to the HTML file to be parsed.
    :type file_path: str
    :return: None
    """
    # Load file
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            content = file.read()
    except FileNotFoundError:
        print(f"Error: File {file_path} not found.")
        return
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return

    # Parse the HTML content
    try:
        soup = BeautifulSoup(content, "html.parser")
        data = {
            "title": (
                soup.title.string
                if soup.title and hasattr(soup.title, "string")
                else "No title found"
            ),
            "headers": [],
        }
        # Extract all element wrapped around <*h></*h> and their subtrees
        for header in soup.find_all(
            [
                "h1",
                "h2",
                "h3",
                "h4",
                "h5",
                "h6",
            ]
        ):
            header_content = {
                "tag": header.name,
                "text": header.get_text(strip=True),
                "html": str(header),
            }
            data["headers"].append(header_content)
    except Exception as e:
        print(f"Error parsing HTML content from {file_path}: {e}")
        return

    # Save extracted data as .json
    json_filename = os.path.basename(file_path).replace(".html", ".json")
    json_folder = os.path.join(RAG_DIR, "crawl_temp/processed_text")
    if not os.path.exists(json_folder):
        os.makedirs(json_folder)
    json_path = os.path.join(json_folder, json_filename)

    try:
        with open(json_path, "w", encoding="utf-8") as json_file:
            json.dump(data, json_file, indent=4)
        print(f"Extracted data save to {json_path}")
    except Exception as e:
        print(f"Error saving JSON to {json_path}: {e}")


def load_JSON_files(folder_path):
    """
    Load JSON files from a directory and parse them into Document objects.

    :param folder_path: Path to the directory containing JSON files.
    :type folder_path: str
    :return: List of Document objects with parsed content and metadata.
    :rtype: list
    """
    JSON_files = []
    for filename in os.listdir(folder_path):
        if filename.endswith(".json"):
            file_path = os.path.join(folder_path, filename)
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    # Extract header texts from the JSON structure
                    for header in data.get("headers", []):
                        text = header.get("text", "")
                        if text:
                            JSON_files.append(
                                Document(
                                    page_content=text, metadata={"source": filename}
                                )
                            )
            except Exception as e:
                print(f"Error loading {file_path}: {e}")
                continue
    return JSON_files


# TODO make this works anywhere
def refine_text():
    """
    Execute the process of loading, parsing, and saving HTML content as JSON.

    :return: None
    """
    # Load HTML files from "html_files" directory
    html_files_dir = os.path.join(RAG_DIR, "crawl_temp/html_files")
    html_files = load_html_files(html_files_dir)

    # Parse and save JSON content for each HTML file individually
    for html_file in html_files:
        parse_and_save(html_file)


# Main Function
def main():
    refine_text()


if __name__ == "__main__":
    main()
