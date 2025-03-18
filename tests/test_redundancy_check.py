"""
Unit tests for the redundancy_check module.
"""

import os
import unittest
from unittest.mock import mock_open, patch

from indigobot.config import TRACKED_URLS_FILE
from indigobot.utils.etl.redundancy_check import check_duplicate, file_to_list


class TestRedundancyCheck(unittest.TestCase):
    """Test cases for the redundancy_check module functions."""

    @patch("indigobot.utils.etl.redundancy_check.file_to_list")
    def test_check_duplicate_new_urls(self, mock_file_to_list):
        """Test check_duplicate with new URLs."""
        # Setup mock
        mock_file_to_list.return_value = ["https://example.com/old"]

        # Test data
        urls = ["https://example.com/new1", "https://example.com/new2"]

        # Mock open to avoid actual file operations
        with patch("builtins.open", mock_open()) as mock_file:
            result = check_duplicate(urls)

            # Verify the result
            self.assertEqual(result, urls)
            # Verify the file was opened for writing
            mock_file.assert_called_once_with(TRACKED_URLS_FILE, "w")
            # Verify write was called for each URL (old + new)
            handle = mock_file()
            self.assertEqual(handle.write.call_count, 3)

    @patch("indigobot.utils.etl.redundancy_check.file_to_list")
    def test_check_duplicate_mixed_urls(self, mock_file_to_list):
        """Test check_duplicate with a mix of new and existing URLs."""
        # Setup mock
        mock_file_to_list.return_value = [
            "https://example.com/old",
            "https://example.com/existing",
        ]

        # Test data
        urls = ["https://example.com/existing", "https://example.com/new"]

        # Mock open to avoid actual file operations
        with patch("builtins.open", mock_open()) as mock_file:
            result = check_duplicate(urls)

            # Verify the result (only new URLs)
            self.assertEqual(result, ["https://example.com/new"])
            # Verify the file was opened for writing
            mock_file.assert_called_once_with(TRACKED_URLS_FILE, "w")
            # Verify write was called for each URL (2 old + 1 new)
            handle = mock_file()
            self.assertEqual(handle.write.call_count, 3)

    @patch("indigobot.utils.etl.redundancy_check.file_to_list")
    def test_check_duplicate_all_existing(self, mock_file_to_list):
        """Test check_duplicate when all URLs already exist."""
        # Setup mock
        mock_file_to_list.return_value = [
            "https://example.com/1",
            "https://example.com/2",
        ]

        # Test data
        urls = ["https://example.com/1", "https://example.com/2"]

        # Mock open to avoid actual file operations
        with patch("builtins.open", mock_open()) as mock_file:
            result = check_duplicate(urls)

            # Verify the result (empty list since all URLs exist)
            self.assertEqual(result, [])
            # Verify the file was opened for writing
            mock_file.assert_called_once_with(TRACKED_URLS_FILE, "w")
            # Verify write was called for each existing URL
            handle = mock_file()
            self.assertEqual(handle.write.call_count, 2)

    @patch(
        "indigobot.utils.etl.redundancy_check.file_to_list",
        side_effect=FileNotFoundError,
    )
    def test_check_duplicate_file_not_found(self, mock_file_to_list):
        """Test check_duplicate when tracked URLs file doesn't exist."""
        # Test data
        urls = ["https://example.com/1", "https://example.com/2"]

        # Mock open to avoid actual file operations
        with patch("builtins.open", mock_open()) as mock_file:
            result = check_duplicate(urls)

            # Verify the result (all URLs are considered new)
            self.assertEqual(result, urls)
            # Verify the file was opened for writing
            mock_file.assert_called_once_with(TRACKED_URLS_FILE, "w")
            # Verify write was called for each URL
            handle = mock_file()
            self.assertEqual(handle.write.call_count, 2)

    def test_file_to_list(self):
        """Test file_to_list function."""
        # Mock data
        file_content = "https://example.com/1\nhttps://example.com/2\n"

        # Mock open to return our test data
        with patch("builtins.open", mock_open(read_data=file_content)) as mock_file:
            result = file_to_list()

            # Verify the result
            self.assertEqual(result, ["https://example.com/1", "https://example.com/2"])
            # Verify the file was opened for reading
            mock_file.assert_called_once_with(TRACKED_URLS_FILE, "r")


if __name__ == "__main__":
    unittest.main()
