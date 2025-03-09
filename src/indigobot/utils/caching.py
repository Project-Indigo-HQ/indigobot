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

CACHE_THRESHOLD = 2


def get_cache_connection():
    """Establish a connection to the SQLite cache database and ensure the cache table exists.

    This function connects to the SQLite database specified by `CACHE_DB` and creates
    a table `response_cache` if it does not already exist. The table stores hashed
    queries as keys and their corresponding responses.

    :return: A connection object to the SQLite database.
    :rtype: sqlite3.Connection
    """
    conn = sqlite3.connect(CACHE_DB)
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS response_cache (
            query_hash TEXT PRIMARY KEY,
            response TEXT,
            query_count INTEGER DEFAULT 0
        )
    """
    )
    conn.commit()
    return conn


def cache_response(query: str, response: str):
    """Store a query-response pair in the cache.

    This function hashes the query and stores it alongside the response in the
    SQLite cache database. If a response for the query already exists, it is replaced.

    :param query: The original user query.
    :type query: str
    :param response: The response to be stored in the cache.
    :type response: str
    """
    conn = get_cache_connection()
    cursor = conn.cursor()
    query_hash = hashlib.sha256(query.encode()).hexdigest()

    cursor.execute(
        "SELECT query_count FROM response_cache WHERE query_hash = ?", (query_hash,)
    )
    result = cursor.fetchone()

    if result and result[0] >= CACHE_THRESHOLD:
        cursor.execute(
            "UPDATE response_cache SET response = ? WHERE query_hash = ?",
            (response, query_hash),
        )
        conn.commit()

    conn.close()


def get_cached_response(query: str) -> str | None:
    """Retrieve a cached response for a given query if available.

    If the query exists but hasn't reached the `CACHE_THRESHOLD`, it increments the count.
    Once the count reaches the threshold, the response is cached.

    :param query: The original user query.
    :type query: str
    :return: The cached response if found, otherwise None.
    :rtype: str | None
    """
    conn = get_cache_connection()
    cursor = conn.cursor()
    query_hash = hashlib.sha256(query.encode()).hexdigest()

    cursor.execute(
        "SELECT response, query_count FROM response_cache WHERE query_hash = ?",
        (query_hash,),
    )
    result = cursor.fetchone()

    if result:
        response, count = result
        if count < CACHE_THRESHOLD:
            cursor.execute(
                "UPDATE response_cache SET query_count = query_count + 1 WHERE query_hash = ?",
                (query_hash,),
            )
            conn.commit()
            conn.close()
            return None
        conn.close()
        return response

    cursor.execute(
        "INSERT INTO response_cache (query_hash, response, query_count) VALUES (?, ?, ?)",
        (query_hash, None, 1),
    )
    conn.commit()
    conn.close()
    return None
