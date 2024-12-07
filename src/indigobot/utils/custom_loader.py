"""
This module is the customized document loader for the chatbot program. 
It uses PyPDFLoader as a PDF loader and Chroma as a vector database.
It loads local PDFs, Python files, and also checks web pages to scrape and consume data.
"""

import os
import re

import unidecode
from bs4 import BeautifulSoup
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import AsyncHtmlLoader
from langchain_community.document_loaders.recursive_url_loader import RecursiveUrlLoader

from indigobot.config import RAG_DIR, r_url_list, url_list, vectorstores
from indigobot.utils.jf_crawler import crawl
from indigobot.utils.refine_html import refine_text, load_JSON_files


def clean_text(text):
    """
    Replaces unicode characters and strips extra whitespace from text.

    :param text: Text to clean.
    :type text: str
    :return: Cleaned text.
    :rtype: str
    """
    text = unidecode.unidecode(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def clean_documents(documents):
    """
    Cleans the page_content text of a list of Documents.

    :param documents: List of documents to clean.
    :type documents: list
    :return: List of cleaned documents.
    :rtype: list
    """
    for doc in documents:
        doc.page_content = clean_text(doc.page_content)
    return documents


def chunking(documents):
    """
    Splits text of documents into chunks.

    :param documents: List of documents to split.
    :type documents: list
    :return: List of text chunks.
    :rtype: list
    """
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=10000, chunk_overlap=1000)
    chunks = text_splitter.split_documents(documents)
    return chunks


def load_docs(docs, vectorstore):
    """
    Split text of arg documents into chunks and load them into the Chroma vector store

    :param docs: List of documents to load and split.
    :type docs: list
    :param vectorstore: The vector store to load documents into.
    :type vectorstore: object
    """

    chunks = chunking(docs)
    add_docs(vectorstore, chunks, 300)


def load_urls(urls, vectorstore):
    """
    Use AsyncHtmlLoader library to check and scrape websites then load to Chroma

    :param urls: List of URLs to load documents from.
    :type urls: list
    :param vectorstore: The vector store to load documents into.
    :type vectorstore: object
    """
    load_docs(AsyncHtmlLoader(urls).load(), vectorstore)


def extract_text(html):
    """
    Extracts text from a div tag with id of 'main' from HTML content.

    :param html: HTML content to parse.
    :type html: str
    :return: Extracted text.
    :rtype: str
    """
    soup = BeautifulSoup(html, "html.parser")
    div_main = soup.find("div", {"id": "main"})
    if div_main:
        return div_main.get_text(" ", strip=True)
    return " ".join(soup.stripped_strings)


def scrape_main(url, depth):
    """
    Recursively scrapes a URL and returns Documents.

    :param url: The base URL to scrape.
    :type url: str
    :param depth: The depth of recursion for scraping.
    :type depth: int
    :return: List of cleaned documents.
    :rtype: list
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


def add_docs(vectorstore, chunks, n):
    """
    Adds documents to the vectorstore database.

    :param vectorstore: The vector store to add documents to.
    :type vectorstore: object
    :param chunks: List of document chunks to add.
    :type chunks: list
    :param n: Number of documents to add per batch.
    :type n: int
    """
    for i in range(0, len(chunks), n):
        vectorstore.add_documents(chunks[i : i + n])


def scrape_urls(urls, vectorstore):
    """
    Processes a list of URLs, scrapes them, and adds them to the vector database.

    :param urls: List of URLs to process and scrape.
    :type urls: list
    :param vectorstore: The vector store to load documents into.
    :type vectorstore: object
    """
    for url in urls:
        docs = scrape_main(url, 12)
        chunks = chunking(docs)
        add_docs(vectorstore, chunks, 300)


def jf_loader(vectorstore):
    """
    Fetches and refines documents from the website source and loads them into the vector database.
    """

    # Fetching document from website then save to for further process
    crawl()

    # # Refine text by removing meanless conent from the XML files
    refine_text()

    # Load the content into vectorstore database
    JSON_DOCS_DIR = os.path.join(RAG_DIR, "crawl_temp/processed_text")
    json_docs = load_JSON_files(JSON_DOCS_DIR)
    print(f"Loaded {len(json_docs)} documents.")

    load_docs(json_docs, vectorstore)


def start_loader():
    """
    Execute the document loading process by scraping web pages, reading PDFs, and loading local files.
    """
    for vectorstore in vectorstores.values():
        try:
            scrape_urls(r_url_list, vectorstore)
            load_urls(url_list, vectorstore)
            jf_loader(vectorstore)
        except Exception as e:
            print(f"Error loading vectorstore: {e}")
            raise


if __name__ == "__main__":
    try:
        start_loader()
    except Exception as e:
        print(e)
