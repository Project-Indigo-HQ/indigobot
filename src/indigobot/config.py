"""
Configuration settings for the CfSS application.

This module contains path configurations and URL lists for data scraping operations.
All URL endpoints and file paths used across the application should be defined here.
It also defines dicts for LLMs and vector embeddings.
"""

import os
from typing import Final, List

from langchain_chroma import Chroma
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

llm = ChatOpenAI(model="gpt-4o")

# Directory paths
CURRENT_DIR: Final[str] = os.path.dirname(__file__)
RAG_DIR: Final[str] = os.path.join(CURRENT_DIR, "rag_data")
CRAWL_TEMP = os.path.join(RAG_DIR, "crawl_temp")
HTML_DIR = os.path.join(CRAWL_TEMP, "html_files")
JSON_DOCS_DIR = os.path.join(CRAWL_TEMP, "processed_text")
TRACKED_URLS_FILE: Final[str] = os.path.join(RAG_DIR, "tracked_urls.txt")
CHROMA_DIR: Final[str] = os.path.join(RAG_DIR, ".chromadb")
SQL_DB: Final[str] = os.path.join(CHROMA_DIR, "chroma.sqlite3")
CACHE_DB: Final[str] = os.path.join(RAG_DIR, "chat_cache.db")
CRAWLER_DIR: Final[str] = os.path.join(CURRENT_DIR, "utils/jf_crawler")

try:
    vectorstore = Chroma(
        persist_directory=CHROMA_DIR,
        embedding_function=OpenAIEmbeddings(model="text-embedding-3-large"),
    )
except Exception as e:
    print(f"Error initializing OpenAI vectorstore: {e}")
    raise

# URLs for API endpoints that return JSON data
url_list: List[str] = [
    "https://rosecityresource.streetroots.org/api/query",  # Street Roots Resource API
]

# URLs for web pages that need recursive scraping
r_url_list: List[str] = [
    "https://www.multco.us/food-assistance/get-food-guide",  # Food assistance guide
    "https://www.multco.us/dchs/rent-housing-shelter",  # Housing and shelter
    "https://www.multco.us/veterans",  # Veterans services
    "https://www.multco.us/dd",  # Developmental disabilities
]

# URLs for web pages that need recursive scraping from https://www.clackamas.us/
cls_url_list: List[str] = [
    "https://www.clackamas.us/guide/low-income-services",  # low income help
    "https://www.clackamas.us/guide/housing-resources",  # Housing
    "https://www.clackamas.us/guide/seniors-and-older-adults",  # Senior assistance
]

# Sitemap URLs
sitemaps: List[str] = [
    "https://centralcityconcern.org/housing-sitemap.xml",
    "https://centralcityconcern.org/healthcare-sitemap.xml",
    "https://centralcityconcern.org/recovery-sitemap.xml",
    "https://centralcityconcern.org/jobs-sitemap.xml",
]

# A series of URLs for test
url_list_XML: List[str] = [
    "https://cameronscrusaders.org/amazing-charities-that-help-with-medical-bills/"  # help with medical bills
]
