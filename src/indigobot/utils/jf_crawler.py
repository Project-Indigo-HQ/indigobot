"""
This module implements a web crawler with built-in retry mechanisms and polite
crawling behavior. It can process XML sitemaps, extract URLs, and download HTML
content while respecting rate limits and server constraints.
The crawler implements best practices for web scraping including user-agent identification,
rate limiting, error handling, retry logic, and content verification.
"""

import os
import random
import time
import xml.etree.ElementTree as ET

import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

from indigobot.config import CRAWL_TEMP, HTML_DIR, sitemaps
from indigobot.utils.redundancy_check import check_duplicate


def start_session():
    """
    Create and configure a REST session with retry mechanisms and backoff.

    :return: A configured requests Session object ready for making HTTP requests
    :rtype: requests.Session
    :raises ImportError: If the requests package is not available
    """
    session = requests.Session()
    retries = Retry(
        total=5, backoff_factor=1, status_forcelist=[403, 500, 502, 503, 504]
    )
    session.mount("https://", HTTPAdapter(max_retries=retries))
    return session


def fetch_xml(url, session):
    """
    Fetch XML content from a given URL using a session with retries.

    :param url: The URL to fetch XML content from
    :type url: str
    :param session: The requests session to use for fetching
    :type session: requests.Session
    :return: Raw XML content from the response
    :rtype: bytes
    :raises requests.exceptions.RequestException: If the request fails after retries
    :raises Exception: If response status code is not 200
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    response = session.get(url, headers=headers)
    if response.status_code == 200:
        time.sleep(5)
        return response.content
    else:
        raise Exception(
            f"Failed to fetch XML from {url}, Status Code: {response.status_code}"
        )


def extract_xml(xml):
    """
    Parse XML content from a sitemap to extract URLs.

    :param xml: Raw XML content from a sitemap
    :type xml: bytes
    :return: List of URLs found in the sitemap
    :rtype: list[str]
    :raises xml.etree.ElementTree.ParseError: If XML parsing fails
    :raises AttributeError: If expected XML elements are not found
    """
    sitemap = ET.fromstring(xml)
    url_list = []
    for url_element in sitemap.findall(
        ".//{http://www.sitemaps.org/schemas/sitemap/0.9}url"
    ):  # Iterate through each <url> tag
        loc = url_element.find(
            "{http://www.sitemaps.org/schemas/sitemap/0.9}loc"
        ).text  # Get the <loc> tag value
        url_list.append(loc)
    return url_list


def load_urls(folder_path):
    """
    Load URLs from all text files in a specified folder.

    :param folder_path: Path to folder containing URL text files
    :type folder_path: str
    :return: Combined list of URLs from all text files
    :rtype: list[str]
    :raises FileNotFoundError: If folder_path doesn't exist
    :raises IOError: If there are problems reading the files
    :raises UnicodeDecodeError: If files aren't valid UTF-8
    """
    urls = []
    for filename in os.listdir(folder_path):
        if filename.endswith(".txt"):
            file_path = os.path.join(folder_path, filename)
            with open(file_path, "r", encoding="utf-8") as file:
                urls.extend(file.read().splitlines())
    return urls


def download_and_save_html(urls, session):
    """
    Download HTML content from URLs and save to files.

    :param urls: List of URLs to download HTML from
    :type urls: list[str]
    :param session: Requests session for making HTTP requests
    :type session: requests.Session
    :raises OSError: If directory creation or file writing fails
    :raises requests.exceptions.RequestException: If downloads fail
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    for url in urls:
        time.sleep(random.randint(3, 6))
        response = session.get(url, headers=headers)

        if response.status_code == 200:
            try:
                # Extract last section of url as file name
                filename = url.rstrip("/").split("/")[-1] + ".html"

                os.makedirs(HTML_DIR, exist_ok=True)

                # save the content to html
                with open(
                    os.path.join(HTML_DIR, filename), "w", encoding="utf-8"
                ) as file:
                    file.write(response.text)
                    print(f"Save html content to {HTML_DIR}")
            except Exception as e:
                print(f"Error extracting html: {e}")
        else:
            print(f"Failed to fetch {url}, Status code: {response.status_code}")


def parse_url_and_save(sitemap_url, target_file_name, session):
    """
    Parse URLs from a sitemap XML and save them to a text file.

    :param sitemap_url: URL of the sitemap to parse
    :type sitemap_url: str
    :param target_file_name: Name for output file (without .txt extension)
    :type target_file_name: str
    :param session: Requests session for fetching sitemap
    :type session: requests.Session
    :raises OSError: If directory creation or file writing fails
    :raises Exception: If sitemap fetching or parsing fails
    """
    urls = extract_xml(fetch_xml(sitemap_url, session))

    # Output all housing URLs
    print("Extracted Housing URLs:")
    for url in urls:
        print(url)

    # Ensure 'urls' directory exists
    extracted_urls = os.path.join(CRAWL_TEMP, "extracted_urls")
    os.makedirs(extracted_urls, exist_ok=True)

    # Save URLs to a file
    with open(f"crawl_temp/extracted_urls/{target_file_name}.txt", "w") as file:
        for url in urls:
            file.write(url + "\n")
    time.sleep(5)


def parse_url(sitemap_url, session):
    """
    Parse URLs from a sitemap XML and return them as a list.

    :param sitemap_url: URL of the sitemap to parse
    :type sitemap_url: str
    :param session: Requests session for fetching sitemap
    :type session: requests.Session
    :return: List of URLs extracted from sitemap
    :rtype: list[str]
    :raises requests.exceptions.RequestException: If sitemap fetch fails
    :raises xml.etree.ElementTree.ParseError: If XML parsing fails
    """
    urls = []
    page_content = extract_xml(fetch_xml(sitemap_url, session))

    # Display all  URLs
    print("Extracting URLs:")
    for url in page_content:
        print(url)
        urls.append(url)

    return urls


def crawl():
    """
    Orchestrate the complete website crawling process.

    :raises Exception: If critical crawling operations fail
    :raises OSError: If file operations fail
    :raises requests.exceptions.RequestException: If HTTP requests fail
    """

    session = start_session()

    download_and_save_html(sitemaps, session)


def main():
    """
    Main entry point for running the crawler as a standalone script.

    :raises SystemExit: If critical errors occur during crawling
    """
    crawl()


if __name__ == "__main__":
    main()
