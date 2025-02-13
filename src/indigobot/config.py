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
CHROMA_DIR: Final[str] = os.path.join(RAG_DIR, ".chromadb")
CACHE_DB: Final[str] = os.path.join(RAG_DIR, "chat_cache.db")
GEM_DB: Final[str] = os.path.join(CHROMA_DIR, "gemini/chroma.sqlite3")
GPT_DB: Final[str] = os.path.join(CHROMA_DIR, "openai/chroma.sqlite3")
CRAWLER_DIR: Final[str] = os.path.join(CURRENT_DIR, "utils/jf_crawler")

# OpenAI embeddings
try:
    vectorstore = Chroma(
        persist_directory=os.path.join(CHROMA_DIR, "openai"),
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

# Sitemap URLs
sitemaps: List[str] = [
    "https://centralcityconcern.org/housing-sitemap.xml",
    "https://centralcityconcern.org/healthcare-sitemap.xml",
    "https://centralcityconcern.org/recovery-sitemap.xml",
    "https://centralcityconcern.org/jobs-sitemap.xml",
]
