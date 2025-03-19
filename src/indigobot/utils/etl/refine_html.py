"""
This module provides functionality for processing HTML files and converting them into
a more structured JSON format. It extracts meaningful content like titles and headers
while preserving the document structure.
The processed documents maintain metadata about their source and structure while
making the content more accessible for NLP tasks.
"""

import json
import os

from bs4 import BeautifulSoup
from langchain.schema import Document

from indigobot.config import HTML_DIR, JSON_DOCS_DIR


def load_html_files(folder_path):
    """
    Load all HTML files from a specified directory.

    :param folder_path: Path to the directory containing HTML files
    :type folder_path: str
    :return: List of absolute paths to HTML files
    :rtype: list[str]
    :raises OSError: If the folder_path doesn't exist or isn't accessible
    :raises TypeError: If folder_path is not a string
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

    :param file_path: Path to the HTML file to be parsed
    :type file_path: str
    :return: None
    :raises FileNotFoundError: If the input file doesn't exist
    :raises OSError: If there are issues reading the file or creating output directory
    :raises Exception: If HTML parsing fails or JSON serialization fails
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
        # Extract all headers and paragraphs
        for element in soup.find_all(
            [
                "h1",
                "h2",
                "h3",
                "h4",
                "h5",
                "h6",
            ]
        ):
            content = {
                "tag": element.name,
                "text": element.get_text(strip=False),
                "html": str(element),
            }
            data["headers"].append(content)
    except Exception as e:
        print(f"Error parsing HTML content from {file_path}: {e}")
        return

    # Save extracted data as .json
    json_filename = os.path.basename(file_path).replace(".html", ".json")
    os.makedirs(JSON_DOCS_DIR, exist_ok=True)
    json_path = os.path.join(JSON_DOCS_DIR, json_filename)

    try:
        with open(json_path, "w", encoding="utf-8") as json_file:
            json.dump(data, json_file, indent=4)
    except Exception as e:
        print(f"Error saving JSON to {json_path}: {e}")


def load_JSON_files(folder_path):
    """
    Load JSON files from a directory and parse them into Document objects.
    Each Document object contains:
    - page_content: The extracted text from headers
    - metadata: A dictionary with 'source' set to the original filename

    :param folder_path: Path to the directory containing JSON files
    :type folder_path: str
    :return: List of Document objects with parsed content and metadata
    :rtype: list[Document]
    :raises OSError: If the folder_path doesn't exist or isn't accessible
    :raises json.JSONDecodeError: If any JSON file is malformed
    :raises Exception: If Document creation fails
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


def refine_text():
    """
    Execute the process of loading, parsing, and saving HTML content as JSON.

    :return: None
    :raises Exception: If the HTML processing pipeline fails at any stage
    """
    # Load HTML files from "html_files" directory
    os.makedirs(HTML_DIR, exist_ok=True)
    html_files = load_html_files(HTML_DIR)

    # Parse and save JSON content for each HTML file individually
    for html_file in html_files:
        parse_and_save(html_file)


# Main Function
def main():
    """
    Main entry point for the HTML refinement process.

    :return: None
    :raises SystemExit: If critical errors occur during processing
    """
    refine_text()


if __name__ == "__main__":
    main()
