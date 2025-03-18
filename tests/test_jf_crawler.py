"""
Unit tests for the jf_crawler module.
"""

import os
import unittest
import xml.etree.ElementTree as ET
from unittest.mock import MagicMock, mock_open, patch

from indigobot.config import HTML_DIR
from indigobot.utils.etl.jf_crawler import (
    crawl,
    download_and_save_html,
    extract_xml,
    fetch_xml,
    main,
    parse_url,
    start_session,
)


class TestJfCrawler(unittest.TestCase):
    """Test cases for the jf_crawler module functions."""

    def test_start_session(self):
        """Test start_session function."""
        # Patch the Session class directly in the module being tested
        with patch("indigobot.utils.etl.jf_crawler.Session") as mock_session:
            # Setup mocks
            session_instance = MagicMock()
            mock_session.return_value = session_instance

            # Patch the other dependencies
            with patch("indigobot.utils.etl.jf_crawler.HTTPAdapter") as mock_adapter:
                with patch("indigobot.utils.etl.jf_crawler.Retry") as mock_retry:
                    adapter_instance = MagicMock()
                    mock_adapter.return_value = adapter_instance
                    retry_instance = MagicMock()
                    mock_retry.return_value = retry_instance

                    # Call the function
                    result = start_session()

                    # Verify the result
                    self.assertEqual(result, session_instance)
                    mock_retry.assert_called_once_with(
                        total=5,
                        backoff_factor=1,
                        status_forcelist=[403, 500, 502, 503, 504],
                    )
                    mock_adapter.assert_called_once_with(max_retries=retry_instance)
                    session_instance.mount.assert_called_once_with(
                        "https://", adapter_instance
                    )

    @patch("time.sleep")
    def test_fetch_xml_success(self, mock_sleep):
        """Test fetch_xml function with successful response."""
        # Setup mock
        session = MagicMock()
        response = MagicMock()
        response.status_code = 200
        response.content = b"<xml>test</xml>"
        session.get.return_value = response

        # Call the function
        result = fetch_xml("https://example.com/sitemap.xml", session)

        # Verify the result
        self.assertEqual(result, b"<xml>test</xml>")
        session.get.assert_called_once()
        mock_sleep.assert_called_once_with(5)

    def test_fetch_xml_failure(self):
        """Test fetch_xml function with failed response."""
        # Setup mock
        session = MagicMock()
        response = MagicMock()
        response.status_code = 404
        session.get.return_value = response

        # Call the function and verify it raises an exception
        with self.assertRaises(Exception) as context:
            fetch_xml("https://example.com/sitemap.xml", session)

        self.assertIn("Failed to fetch XML", str(context.exception))
        session.get.assert_called_once()

    def test_extract_xml(self):
        """Test extract_xml function."""
        # Test data - simplified sitemap XML
        xml_content = b"""<?xml version="1.0" encoding="UTF-8"?>
        <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
            <url>
                <loc>https://example.com/page1</loc>
            </url>
            <url>
                <loc>https://example.com/page2</loc>
            </url>
        </urlset>"""

        # Call the function
        result = extract_xml(xml_content)

        # Verify the result
        self.assertEqual(len(result), 2)
        self.assertIn("https://example.com/page1", result)
        self.assertIn("https://example.com/page2", result)

    @patch("os.makedirs")
    @patch("time.sleep")
    def test_download_and_save_html(self, mock_sleep, mock_makedirs):
        """Test download_and_save_html function."""
        # Setup mocks
        session = MagicMock()
        response1 = MagicMock()
        response1.status_code = 200
        response1.text = "<html>content1</html>"
        response2 = MagicMock()
        response2.status_code = 404
        session.get.side_effect = [response1, response2]

        # Test data
        urls = ["https://example.com/page1", "https://example.com/page2"]

        # Mock open to avoid actual file operations
        with patch("builtins.open", mock_open()) as mock_file:
            # Call the function
            download_and_save_html(urls, session)

            # Verify the function behavior
            mock_makedirs.assert_called_once_with(HTML_DIR, exist_ok=True)
            self.assertEqual(session.get.call_count, 2)
            self.assertEqual(mock_sleep.call_count, 2)
            # Only one file should be written (for the successful response)
            mock_file.assert_called_once()
            handle = mock_file()
            handle.write.assert_called_once_with("<html>content1</html>")

    @patch("indigobot.utils.etl.jf_crawler.fetch_xml")
    @patch("indigobot.utils.etl.jf_crawler.extract_xml")
    def test_parse_url(self, mock_extract_xml, mock_fetch_xml):
        """Test parse_url function."""
        # Setup mocks
        mock_fetch_xml.return_value = b"<xml>test</xml>"
        mock_extract_xml.return_value = [
            "https://example.com/page1",
            "https://example.com/page2",
        ]
        session = MagicMock()

        # Call the function
        result = parse_url("https://example.com/sitemap.xml", session)

        # Verify the result
        self.assertEqual(
            result, ["https://example.com/page1", "https://example.com/page2"]
        )
        mock_fetch_xml.assert_called_once_with(
            "https://example.com/sitemap.xml", session
        )
        mock_extract_xml.assert_called_once_with(b"<xml>test</xml>")

    @patch("indigobot.utils.etl.jf_crawler.start_session")
    @patch("indigobot.utils.etl.jf_crawler.check_duplicate")
    @patch("indigobot.utils.etl.jf_crawler.parse_url")
    @patch("indigobot.utils.etl.jf_crawler.download_and_save_html")
    def test_crawl_with_new_urls(
        self, mock_download, mock_parse_url, mock_check_duplicate, mock_start_session
    ):
        """Test crawl function with new URLs to process."""
        # Setup mocks
        session = MagicMock()
        mock_start_session.return_value = session
        mock_check_duplicate.return_value = ["https://example.com/sitemap.xml"]
        mock_parse_url.return_value = [
            "https://example.com/page1",
            "https://example.com/page2",
        ]

        # Call the function
        result = crawl()

        # Verify the result and function behavior
        self.assertTrue(result)
        mock_start_session.assert_called_once()
        mock_check_duplicate.assert_called_once()
        mock_parse_url.assert_called_once_with(
            "https://example.com/sitemap.xml", session
        )
        mock_download.assert_called_once_with(
            ["https://example.com/page1", "https://example.com/page2"], session
        )

    @patch("indigobot.utils.etl.jf_crawler.start_session")
    @patch("indigobot.utils.etl.jf_crawler.check_duplicate")
    def test_crawl_no_new_urls(self, mock_check_duplicate, mock_start_session):
        """Test crawl function with no new URLs to process."""
        # Setup mocks
        session = MagicMock()
        mock_start_session.return_value = session
        mock_check_duplicate.return_value = []  # No new URLs

        # Call the function
        result = crawl()

        # Verify the result and function behavior
        self.assertFalse(result)
        mock_start_session.assert_called_once()
        mock_check_duplicate.assert_called_once()

    @patch("indigobot.utils.etl.jf_crawler.crawl")
    def test_main(self, mock_crawl):
        """Test main function."""
        # Call the function
        main()

        # Verify the function behavior
        mock_crawl.assert_called_once()


if __name__ == "__main__":
    unittest.main()
