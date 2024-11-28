"""
This module is the customized document loader for the chatbot. 
It uses PyPDFLoader as a PDF loader and Chroma as a vector database.
It loads local PDFs, Python files, and also checks web pages to scrape and consume data.
"""

import re
import ssl

import unidecode
from bs4 import BeautifulSoup
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import AsyncHtmlLoader
from langchain_community.document_loaders.recursive_url_loader import RecursiveUrlLoader
from langchain_community.document_transformers import BeautifulSoupTransformer

from indigobot.config import urls, r_urls, vectorstores

vectorstores = (vectorstores["gpt"], vectorstores["gemini"])


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
    """
    chunks = chunking(docs)
    add_documents(vectorstore, chunks, 300)


def load_urls(urls, vectorstore):
    """
    Use AsyncHtmlLoader library to check and scrape websites then load to Chroma

    :param urls: List of URLs to load documents from.
    :type urls: list
    """
    load_docs(AsyncHtmlLoader(urls).load(), vectorstore)


def scrape_articles(links):
    """
    Scrapes a list of links, extracts article text, and returns Documents.

    :param links: List of URLs to scrape.
    :type links: list
    :return: List of transformed documents.
    :rtype: list
    """
    # Create SSL context with verification disabled
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False  # Disable hostname checking
    ssl_context.verify_mode = ssl.CERT_NONE  # Disable certificate verification
    loader = AsyncHtmlLoader(links, requests_kwargs={"ssl": ssl_context})
    docs = loader.load()
    # Extract article tag
    transformer = BeautifulSoupTransformer()
    docs_tr = transformer.transform_documents(documents=docs, tags_to_extract=[])
    clean_documents(docs_tr)
    return docs_tr


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


def add_documents(vectorstore, chunks, n):
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


def scrape_urls(url_list, vectorstore):
    """
    Processes a list of URLs, scrapes them, and adds them to the vector database.

    :param url_list: List of URLs to process and scrape.
    """
    for url in url_list:
        docs = scrape_main(url, 12)
        chunks = chunking(docs)
        add_documents(vectorstore, chunks, 300)


def main():
    """
    Execute the document loading process by scraping web pages, reading PDFs, and loading local files.
    """
    for vectorstore in vectorstores:
        try:
            scrape_urls(r_urls, vectorstore)
            load_urls(urls, vectorstore)
        except Exception as e:
            print(f"Error loading vectorstore: {e}")
            raise


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(e)
