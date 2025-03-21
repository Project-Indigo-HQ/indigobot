"""
Unit tests for the caching module.

This module contains tests for the functions in the indigobot.utils.caching module.
"""

import hashlib
import unittest
from unittest.mock import MagicMock, patch

import pytest

from indigobot.utils.caching import (
    CACHE_THRESHOLD,
    cache_response,
    get_cache_connection,
    get_cached_response,
)


class TestCachingModule(unittest.TestCase):
    """Test cases for the caching module functions."""

    @patch("indigobot.utils.caching.sqlite3")
    def test_get_cache_connection(self, mock_sqlite):
        """Test the get_cache_connection function."""
        # Setup
        mock_connection = MagicMock()
        mock_sqlite.connect.return_value = mock_connection

        # Execute
        result = get_cache_connection()

        # Assert
        self.assertEqual(result, mock_connection)
        mock_sqlite.connect.assert_called_once()

    @patch("indigobot.utils.caching.get_cache_connection")
    @patch("indigobot.utils.caching.hashlib.sha256")
    def test_cache_response(self, mock_sha256, mock_get_cache):
        """Test the cache_response function."""
        # Setup
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_get_cache.return_value = mock_conn

        # Mock the hash
        mock_hash = MagicMock()
        mock_hash.hexdigest.return_value = "test_hash"
        mock_sha256.return_value = mock_hash

        # Mock fetchone to return None (no existing entry)
        mock_cursor.fetchone.return_value = None

        # Execute
        cache_response("test query", "test response")

        # Assert
        mock_get_cache.assert_called_once()
        mock_conn.cursor.assert_called_once()
        self.assertGreaterEqual(mock_cursor.execute.call_count, 1)

    @patch("indigobot.utils.caching.get_cache_connection")
    @patch("indigobot.utils.caching.hashlib.sha256")
    def test_get_cached_response_hit(self, mock_sha256, mock_get_cache):
        """Test the get_cached_response function with a cache hit."""
        # Setup
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_get_cache.return_value = mock_conn

        # Mock the hash
        mock_hash = MagicMock()
        mock_hash.hexdigest.return_value = "test_hash"
        mock_sha256.return_value = mock_hash

        # Mock a cache hit with response and count
        mock_cursor.fetchone.return_value = ("cached response", 3)

        # Execute
        result = get_cached_response("test query")

        # Assert
        self.assertEqual(result, "cached response")
        mock_get_cache.assert_called_once()
        mock_conn.cursor.assert_called_once()
        mock_cursor.execute.assert_called_once()

    @patch("indigobot.utils.caching.get_cache_connection")
    @patch("indigobot.utils.caching.hashlib.sha256")
    def test_get_cached_response_miss(self, mock_sha256, mock_get_cache):
        """Test the get_cached_response function with a cache miss."""
        # Setup
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_get_cache.return_value = mock_conn

        # Mock the hash
        mock_hash = MagicMock()
        mock_hash.hexdigest.return_value = "test_hash"
        mock_sha256.return_value = mock_hash

        # Mock a cache miss
        mock_cursor.fetchone.return_value = None

        # Execute
        result = get_cached_response("test query")

        # Assert
        self.assertIsNone(result)
        mock_get_cache.assert_called_once()
        mock_conn.cursor.assert_called_once()
        self.assertGreaterEqual(mock_cursor.execute.call_count, 1)

    @patch("indigobot.utils.caching.get_cache_connection")
    def test_get_cached_response_error(self, mock_get_connection):
        """Test the get_cached_response function with an error."""
        # Setup
        mock_get_connection.side_effect = Exception("Connection error")
        query = "test query"

        # Execute
        with self.assertRaises(Exception):
            get_cached_response(query)

        # Assert
        mock_get_connection.assert_called_once()


if __name__ == "__main__":
    unittest.main()
