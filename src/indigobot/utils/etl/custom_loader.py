"""
A customized document loader for processing and storing various document types.
The module uses Chroma as a vector database for storing processed documents. It includes
utilities for text cleaning, chunking, and batch processing of documents.
"""

import os
import re
from shutil import rmtree

import unidecode
from bs4 import BeautifulSoup
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import AsyncHtmlLoader
from langchain_community.document_loaders.recursive_url_loader import RecursiveUrlLoader

from indigobot.config import (
    CRAWL_TEMP,
    JSON_DOCS_DIR,
    cls_url_list,
    r_url_list,
    url_list,
    vectorstore,
)
from indigobot.utils.etl.jf_crawler import crawl
from indigobot.utils.etl.redundancy_check import check_duplicate
from indigobot.utils.etl.refine_html import load_JSON_files, refine_text

chunk_size = 512
chunk_overlap = 10


def clean_text(text):
    """
    Replaces unicode characters and strips extra whitespace from text.

    :param text: Raw text content to be cleaned
    :type text: str
    :return: Text with unicode characters replaced and whitespace normalized
    :rtype: str
    :raises UnicodeError: If unicode replacement fails
    """
    text = unidecode.unidecode(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def clean_documents(documents):
    """
    Cleans the page_content text of a list of Documents.

    :param documents: List of Document objects to clean
    :type documents: list[Document]
    :return: List of Document objects with cleaned page_content
    :rtype: list[Document]
    :raises AttributeError: If documents don't have page_content attribute
    """
    for doc in documents:
        doc.page_content = clean_text(doc.page_content)
    return documents


def chunking(documents):
    """
    Uses RecursiveCharacterTextSplitter to break documents into chunks
    of approximately 10000 characters with 1000 character overlap.

    :param documents: List of Document objects to split
    :type documents: list[Document]
    :return: List of Document chunks
    :rtype: list[Document]
    :raises ValueError: If documents cannot be split properly
    """
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size, chunk_overlap=chunk_overlap
    )
    chunks = text_splitter.split_documents(documents)
    return chunks


def load_docs(docs):
    """
    Processes documents by splitting them into chunks and adding chunks to the
    vector store in batches of 300.

    :param docs: List of Document objects to process and load
    :type docs: list[Document]
    :raises Exception: If chunking operations fail
    """

    chunks = chunking(docs)
    add_docs(chunks, 300)


def load_urls(urls):
    """
    Asynchronously load and process web pages from URLs into the vector store.

    :param urls: List of URLs to scrape and process
    :type urls: list[str]
    :raises Exception: If URL loading or processing fails
    """
    try:
        temp_urls = check_duplicate(urls)
        if temp_urls:
            load_docs(AsyncHtmlLoader(temp_urls).load())
    except Exception as e:
        print(f"Error in load_urls: {e}")
        raise


def extract_text(html):
    """
    Extracts text from a div tag with id of 'main' from HTML content.

    :param html: Raw HTML content to parse
    :type html: str
    :return: Extracted text content with normalized spacing
    :rtype: str
    :raises BeautifulSoupError: If HTML parsing fails
    """
    soup = BeautifulSoup(html, "html.parser")
    div_main = soup.find("div", {"id": "main"})
    if div_main:
        return div_main.get_text(" ", strip=True)
    return " ".join(soup.stripped_strings)


def scrape_main(url, depth):
    """
    Recursively scrapes a URL and its linked pages up to specified depth.

    :param url: The base URL to start scraping from
    :type url: str
    :param depth: Maximum recursion depth for following links
    :type depth: int
    :return: List of Document objects with cleaned content
    :rtype: list[Document]
    :raises Exception: If scraping fails or timeout occurs
    """
    loader = RecursiveUrlLoader(
        url=url,
        max_depth=depth,
        timeout=20,
        use_async=True,
        prevent_outside=True,
        check_response_status=True,
        continue_on_failure=True,
        extractor=extract_text,
    )
    docs = loader.load()
    clean_documents(docs)
    return docs


def add_docs(chunks, n):
    """
    Adds document chunks to the vector store in batches.

    :param chunks: List of Document chunks to add
    :type chunks: list[Document]
    :param n: Batch size for adding documents
    :type n: int
    :raises Exception: If vector store operations fail
    """
    for i in range(0, len(chunks), n):
        vectorstore.add_documents(chunks[i : i + n])


def scrape_urls(urls):
    """
    Processes multiple URLs by scraping and loading them into the vector store.

    :param urls: List of URLs to process
    :type urls: list[str]
    :raises Exception: If scraping or processing fails for any URL
    """
    try:
        temp_urls = check_duplicate(urls)
        if temp_urls:
            for url in temp_urls:
                docs = scrape_main(url, 12)
                chunks = chunking(docs)
                add_docs(chunks, 300)
    except Exception as e:
        print(f"Error scraping URLs: {e}")
        raise


def jf_loader():
    """
    Fetches and refines documents from the website source and loads them into the vector database.

    :raises Exception: If crawling, refinement, or loading fails
    """

    # Fetching document from website then save to for further process
    new_url = crawl()

    # If new URLs: refine text by removing meanless conent from the XML files
    if new_url is True:
        refine_text()

        # Load the content into vectorstore database
        os.makedirs(JSON_DOCS_DIR, exist_ok=True)
        json_docs = load_JSON_files(JSON_DOCS_DIR)

        load_docs(json_docs)


def start_loader():
    """
    Execute the document loading process by scraping web pages and loading local files.

    :raises Exception: If loading fails for all vector stores
    """
    try:
        scrape_urls(r_url_list)
        scrape_urls(cls_url_list)
        load_urls(url_list)
        jf_loader()

    except Exception as e:
        print(f"Error loading vectorstore: {e}")
        raise

    if os.path.exists(CRAWL_TEMP):
        rmtree(CRAWL_TEMP)


if __name__ == "__main__":
    try:
        start_loader()
    except Exception as e:
        print(e)
