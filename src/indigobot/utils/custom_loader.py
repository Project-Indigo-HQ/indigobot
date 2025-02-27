"""
A customized document loader for processing and storing various document types.
The module uses Chroma as a vector database for storing processed documents. It includes
utilities for text cleaning, chunking, and batch processing of documents.
"""

import json
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
from indigobot.utils.jf_crawler import crawl
from indigobot.utils.redundancy_check_v2 import check_duplicate_v2
from indigobot.utils.refine_html import load_JSON_files, refine_text


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
    Splits text of documents into smaller chunks for processing.

    :param documents: List of Document objects to split
    :type documents: list[Document]
    :return: List of Document chunks
    :rtype: list[Document]
    :raises ValueError: If documents cannot be split properly
    """
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=10000, chunk_overlap=1000)
    chunks = text_splitter.split_documents(documents)
    return chunks


def load_docs(docs):
    """
    Split text of documents into chunks and load them into the Chroma vector store.

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
    """
    try:
        temp_urls = check_duplicate(urls)
        if temp_urls:
            load_docs(AsyncHtmlLoader(temp_urls).load())
    except Exception as e:
        print(f"Error in load_urls: {e}")
        raise
    """
    try:
        load_docs(AsyncHtmlLoader(urls).load())
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
     Uses RecursiveUrlLoader with async loading and safety checks:
    - Prevents scraping outside the original domain
    - Checks response status codes
    - Uses timeouts to prevent hanging
    - Continues on individual page failures

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
"""
def add_docs_experiment1(chunks, n):
    for i in range(0, len(chunks), n):
        if(check_duplicate_v2(vectorstore, chunks[i])):
            print("Duplicate content found, skipping...")
            continue
        else:
            vectorstore.add_documents(chunks[i])

def add_docs_experiment2(chunks, n):
    for i in range(0, len(chunks), n):
        batch = chunks[i : i + n]
        if any(check_duplicate_v2(vectorstore, doc) for doc in batch):
            print("Duplicate content found, skipping batch")
            continue
        else:
            vectorstore.add_documents(chunks[i])
"""

def scrape_urls(urls):
    """
    Processes multiple URLs by scraping and loading them into the vector store.

    :param urls: List of URLs to process
    :type urls: list[str]
    :raises Exception: If scraping or processing fails for any URL
    """
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
    """
    try:
        for url in urls:
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
        print(f"Loaded {len(json_docs)} documents.")
        
        for doc in json_docs:
            load_docs(doc)

        #load_docs(json_docs)
    else:
        print("no new URLs...")


def start_loader():
    """
    Execute the document loading process by scraping web pages and loading local files.

    :raises Exception: If loading fails for all vector stores
    """
    try:
        scrape_urls(r_url_list)
        #scrape_urls(cls_url_list)
        #load_urls(url_list)
        #jf_loader()

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
