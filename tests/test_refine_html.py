"""
Unit tests for the refine_html module.
"""

import json
import os
import unittest
from unittest.mock import MagicMock, mock_open, patch

from indigobot.config import HTML_DIR, JSON_DOCS_DIR
from indigobot.utils.etl.refine_html import (
    load_html_files,
    load_JSON_files,
    main,
    parse_and_save,
    refine_text,
)


class TestRefineHtml(unittest.TestCase):
    """Test cases for the refine_html module functions."""

    @patch("os.listdir")
    def test_load_html_files(self, mock_listdir):
        """Test load_html_files function."""
        # Mock data
        mock_listdir.return_value = ["file1.html", "file2.txt", "file3.html"]
        folder_path = "/test/path"

        # Call the function
        result = load_html_files(folder_path)

        # Verify the result
        expected = ["/test/path/file1.html", "/test/path/file3.html"]
        self.assertEqual(result, expected)
        mock_listdir.assert_called_once_with(folder_path)

    @patch("os.makedirs")
    def test_parse_and_save_success(self, mock_makedirs):
        """Test parse_and_save function with successful parsing."""
        # Mock data
        file_path = "/test/path/file1.html"
        html_content = (
            "<html><title>Test Title</title><body><h1>Test Header</h1></body></html>"
        )

        # Create mock for file operations
        mock_file = mock_open(read_data=html_content)

        # Mock both file reads and writes
        with patch("builtins.open", mock_file) as mock_open_file:
            # Mock json.dump to avoid actual file operations
            with patch("json.dump") as mock_json_dump:
                # Call the function
                parse_and_save(file_path)

                # Verify the function behavior
                mock_makedirs.assert_called_once_with(JSON_DOCS_DIR, exist_ok=True)
                # Verify the JSON structure contains expected data
                args, _ = mock_json_dump.call_args
                data = args[0]
                self.assertEqual(data["title"], "Test Title")
                self.assertEqual(len(data["headers"]), 1)
                self.assertEqual(data["headers"][0]["tag"], "h1")
                self.assertEqual(data["headers"][0]["text"], "Test Header")

    @patch("builtins.open")
    def test_parse_and_save_file_not_found(self, mock_open):
        """Test parse_and_save function when file is not found."""
        # Setup mock to raise FileNotFoundError
        mock_open.side_effect = FileNotFoundError()

        # Call the function
        parse_and_save("/test/path/nonexistent.html")

        # Verify the function behavior
        mock_open.assert_called_once_with(
            "/test/path/nonexistent.html", "r", encoding="utf-8"
        )

    @patch("os.listdir")
    @patch("builtins.open")
    @patch("json.load")
    def test_load_JSON_files(self, mock_json_load, mock_open, mock_listdir):
        """Test load_JSON_files function."""
        # Mock data
        mock_listdir.return_value = ["file1.json", "file2.txt", "file3.json"]
        mock_json_load.side_effect = [
            {"headers": [{"text": "Header 1"}, {"text": "Header 2"}]},
            {"headers": [{"text": "Header 3"}]},
        ]

        # Call the function
        result = load_JSON_files("/test/path")

        # Verify the result
        self.assertEqual(
            len(result), 3
        )  # 2 headers from file1.json + 1 from file3.json
        self.assertEqual(result[0].page_content, "Header 1")
        self.assertEqual(result[0].metadata["source"], "file1.json")
        self.assertEqual(result[1].page_content, "Header 2")
        self.assertEqual(result[2].page_content, "Header 3")
        self.assertEqual(result[2].metadata["source"], "file3.json")

    @patch("os.listdir")
    @patch("builtins.open")
    @patch("json.load")
    def test_load_JSON_files_with_exception(
        self, mock_json_load, mock_open, mock_listdir
    ):
        """Test load_JSON_files function when an exception occurs."""
        # Mock data
        mock_listdir.return_value = ["file1.json", "file2.txt", "file3.json"]
        mock_json_load.side_effect = [
            Exception("Test exception"),
            {"headers": [{"text": "Header 3"}]},
        ]

        # Call the function
        result = load_JSON_files("/test/path")

        # Verify the result - should only have data from the second file
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].page_content, "Header 3")
        self.assertEqual(result[0].metadata["source"], "file3.json")

    @patch("os.listdir")
    @patch("builtins.open")
    @patch("json.load")
    def test_load_JSON_files_empty_headers(
        self, mock_json_load, mock_open, mock_listdir
    ):
        """Test load_JSON_files function with empty headers."""
        # Mock data
        mock_listdir.return_value = ["file1.json"]
        mock_json_load.return_value = {"headers": []}

        # Call the function
        result = load_JSON_files("/test/path")

        # Verify the result - should be empty
        self.assertEqual(len(result), 0)

    @patch("os.makedirs")
    @patch("indigobot.utils.etl.refine_html.load_html_files")
    @patch("indigobot.utils.etl.refine_html.parse_and_save")
    def test_refine_text(
        self, mock_parse_and_save, mock_load_html_files, mock_makedirs
    ):
        """Test refine_text function."""
        # Mock data
        mock_load_html_files.return_value = [
            "/test/path/file1.html",
            "/test/path/file2.html",
        ]

        # Call the function
        refine_text()

        # Verify the function behavior
        mock_makedirs.assert_called_once_with(HTML_DIR, exist_ok=True)
        mock_load_html_files.assert_called_once_with(HTML_DIR)
        self.assertEqual(mock_parse_and_save.call_count, 2)
        mock_parse_and_save.assert_any_call("/test/path/file1.html")
        mock_parse_and_save.assert_any_call("/test/path/file2.html")

    @patch("indigobot.utils.etl.refine_html.refine_text")
    def test_main(self, mock_refine_text):
        """Test main function."""
        # Call the function
        main()

        # Verify the function behavior
        mock_refine_text.assert_called_once()


if __name__ == "__main__":
    unittest.main()
