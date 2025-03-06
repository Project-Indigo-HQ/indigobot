"""
Module for caching responses to common user questions.

Functions
---------
get_cache_connection
    Establishes a connection to the SQLite cache database and ensures the table exists.
cache_response
    Store a response in the cache.
get_cached_response
    Retrieve a cached response if available.
"""

import hashlib
import sqlite3

from indigobot.config import CACHE_DB


def get_cache_connection():
    """Establish a connection to the SQLite cache database and ensure the cache table exists.

    :return: A connection object to the SQLite database.
    :rtype: sqlite3.Connection
    """
    conn = sqlite3.connect(CACHE_DB)
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS response_cache (
            query_hash TEXT PRIMARY KEY,
            response TEXT
        )
    """
    )
    conn.commit()
    return conn


def cache_response(query: str, response: str):
    """Store a query-response pair in the cache.

    :param query: The original user query.
    :type query: str
    :param response: The response to be stored in the cache.
    :type response: str
    """
    conn = get_cache_connection()
    cursor = conn.cursor()
    query_hash = hashlib.sha256(query.encode()).hexdigest()
    cursor.execute(
        "INSERT OR REPLACE INTO response_cache (query_hash, response) VALUES (?, ?)",
        (query_hash, response),
    )
    conn.commit()
    conn.close()


def get_cached_response(query: str) -> str | None:
    """Retrieve a cached response for a given query if available.

    :param query: The original user query.
    :type query: str
    :return: The cached response if found, otherwise None.
    :rtype: str | None
    """
    conn = get_cache_connection()
    cursor = conn.cursor()
    query_hash = hashlib.sha256(query.encode()).hexdigest()
    cursor.execute(
        "SELECT response FROM response_cache WHERE query_hash = ?", (query_hash,)
    )
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None
