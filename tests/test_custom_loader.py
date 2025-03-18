"""
Unit tests for the custom_loader module.
"""

import os
import re
import unittest
from unittest.mock import MagicMock, mock_open, patch

from langchain.schema import Document

from indigobot.config import CRAWL_TEMP
from indigobot.utils.etl.custom_loader import (
    add_docs,
    chunking,
    clean_documents,
    clean_text,
    extract_text,
    jf_loader,
    load_docs,
    load_urls,
    scrape_main,
    scrape_urls,
    start_loader,
)


class TestCustomLoader(unittest.TestCase):
    """Test cases for the custom_loader module functions."""

    def test_clean_text(self):
        """Test clean_text function."""
        # Test data
        text = "  This is a test\nwith multiple   spaces  and\nnewlines. "

        # Call the function
        result = clean_text(text)

        # Verify the result
        expected = "This is a test with multiple spaces and newlines."
        self.assertEqual(result, expected)

    def test_clean_documents(self):
        """Test clean_documents function."""
        # Test data
        doc1 = Document(
            page_content="  Test1\nwith newlines  ", metadata={"source": "test1"}
        )
        doc2 = Document(
            page_content="  Test2  with spaces  ", metadata={"source": "test2"}
        )
        documents = [doc1, doc2]

        # Call the function
        result = clean_documents(documents)

        # Verify the result
        self.assertEqual(result[0].page_content, "Test1 with newlines")
        self.assertEqual(result[1].page_content, "Test2 with spaces")
        self.assertEqual(result[0].metadata, {"source": "test1"})
        self.assertEqual(result[1].metadata, {"source": "test2"})

    @patch("indigobot.utils.etl.custom_loader.RecursiveCharacterTextSplitter")
    def test_chunking(self, mock_splitter_class):
        """Test chunking function."""
        # Setup mock
        mock_splitter = MagicMock()
        mock_splitter_class.return_value = mock_splitter
        mock_splitter.split_documents.return_value = ["chunk1", "chunk2"]

        # Test data
        documents = [
            Document(page_content="Test document", metadata={"source": "test"})
        ]

        # Call the function
        result = chunking(documents)

        # Verify the result
        self.assertEqual(result, ["chunk1", "chunk2"])
        mock_splitter_class.assert_called_once_with(chunk_size=512, chunk_overlap=10)
        mock_splitter.split_documents.assert_called_once_with(documents)

    @patch("indigobot.utils.etl.custom_loader.chunking")
    @patch("indigobot.utils.etl.custom_loader.add_docs")
    def test_load_docs(self, mock_add_docs, mock_chunking):
        """Test load_docs function."""
        # Setup mocks
        mock_chunking.return_value = ["chunk1", "chunk2"]

        # Test data
        docs = [Document(page_content="Test document", metadata={"source": "test"})]

        # Call the function
        load_docs(docs)

        # Verify the function behavior
        mock_chunking.assert_called_once_with(docs)
        mock_add_docs.assert_called_once_with(["chunk1", "chunk2"], 300)

    @patch("indigobot.utils.etl.custom_loader.check_duplicate")
    @patch("indigobot.utils.etl.custom_loader.AsyncHtmlLoader")
    @patch("indigobot.utils.etl.custom_loader.load_docs")
    def test_load_urls_with_new_urls(
        self, mock_load_docs, mock_loader_class, mock_check_duplicate
    ):
        """Test load_urls function with new URLs."""
        # Setup mocks
        mock_check_duplicate.return_value = ["https://example.com/new"]
        mock_loader = MagicMock()
        mock_loader_class.return_value = mock_loader
        mock_loader.load.return_value = ["doc1", "doc2"]

        # Test data
        urls = ["https://example.com/test"]

        # Call the function
        load_urls(urls)

        # Verify the function behavior
        mock_check_duplicate.assert_called_once_with(urls)
        mock_loader_class.assert_called_once_with(["https://example.com/new"])
        mock_loader.load.assert_called_once()
        mock_load_docs.assert_called_once_with(["doc1", "doc2"])

    @patch("indigobot.utils.etl.custom_loader.check_duplicate")
    @patch("indigobot.utils.etl.custom_loader.AsyncHtmlLoader")
    def test_load_urls_no_new_urls(self, mock_loader_class, mock_check_duplicate):
        """Test load_urls function with no new URLs."""
        # Setup mocks
        mock_check_duplicate.return_value = []  # No new URLs

        # Test data
        urls = ["https://example.com/test"]

        # Call the function
        load_urls(urls)

        # Verify the function behavior
        mock_check_duplicate.assert_called_once_with(urls)
        mock_loader_class.assert_not_called()

    def test_extract_text_with_main_div(self):
        """Test extract_text function with a div#main element."""
        # Test data
        html = '<html><body><div id="main">Main content</div><div>Other content</div></body></html>'

        # Call the function
        result = extract_text(html)

        # Verify the result
        self.assertEqual(result, "Main content")

    def test_extract_text_without_main_div(self):
        """Test extract_text function without a div#main element."""
        # Test data
        html = "<html><body><div>Content 1</div><div>Content 2</div></body></html>"

        # Call the function
        result = extract_text(html)

        # Verify the result
        self.assertEqual(result, "Content 1 Content 2")

    @patch("indigobot.utils.etl.custom_loader.RecursiveUrlLoader")
    @patch("indigobot.utils.etl.custom_loader.clean_documents")
    def test_scrape_main(self, mock_clean_documents, mock_loader_class):
        """Test scrape_main function."""
        # Setup mocks
        mock_loader = MagicMock()
        mock_loader_class.return_value = mock_loader

        # Create Document objects instead of strings
        doc1 = MagicMock()
        doc2 = MagicMock()
        mock_loader.load.return_value = [doc1, doc2]

        # Call the function
        result = scrape_main("https://example.com", 3)

        # Verify the result and function behavior
        self.assertEqual(result, [doc1, doc2])
        mock_loader_class.assert_called_once_with(
            url="https://example.com",
            max_depth=3,
            timeout=20,
            use_async=True,
            prevent_outside=True,
            check_response_status=True,
            continue_on_failure=True,
            extractor=extract_text,
        )
        mock_loader.load.assert_called_once()
        mock_clean_documents.assert_called_once_with([doc1, doc2])

    @patch("indigobot.utils.etl.custom_loader.vectorstore")
    def test_add_docs(self, mock_vectorstore):
        """Test add_docs function."""
        # Test data
        chunks = ["chunk1", "chunk2", "chunk3", "chunk4", "chunk5"]
        n = 2  # Batch size

        # Call the function
        add_docs(chunks, n)

        # Verify the function behavior
        self.assertEqual(mock_vectorstore.add_documents.call_count, 3)
        # First batch: chunks 0-1
        mock_vectorstore.add_documents.assert_any_call(["chunk1", "chunk2"])
        # Second batch: chunks 2-3
        mock_vectorstore.add_documents.assert_any_call(["chunk3", "chunk4"])
        # Third batch: chunk 4
        mock_vectorstore.add_documents.assert_any_call(["chunk5"])

    @patch("indigobot.utils.etl.custom_loader.check_duplicate")
    @patch("indigobot.utils.etl.custom_loader.scrape_main")
    @patch("indigobot.utils.etl.custom_loader.chunking")
    @patch("indigobot.utils.etl.custom_loader.add_docs")
    def test_scrape_urls_with_new_urls(
        self, mock_add_docs, mock_chunking, mock_scrape_main, mock_check_duplicate
    ):
        """Test scrape_urls function with new URLs."""
        # Setup mocks
        mock_check_duplicate.return_value = ["https://example.com/new"]
        mock_scrape_main.return_value = ["doc1", "doc2"]
        mock_chunking.return_value = ["chunk1", "chunk2"]

        # Test data
        urls = ["https://example.com/test"]

        # Call the function
        scrape_urls(urls)

        # Verify the function behavior
        mock_check_duplicate.assert_called_once_with(urls)
        mock_scrape_main.assert_called_once_with("https://example.com/new", 12)
        mock_chunking.assert_called_once_with(["doc1", "doc2"])
        mock_add_docs.assert_called_once_with(["chunk1", "chunk2"], 300)

    @patch("indigobot.utils.etl.custom_loader.check_duplicate")
    def test_scrape_urls_no_new_urls(self, mock_check_duplicate):
        """Test scrape_urls function with no new URLs."""
        # Setup mocks
        mock_check_duplicate.return_value = []  # No new URLs

        # Test data
        urls = ["https://example.com/test"]

        # Call the function
        scrape_urls(urls)

        # Verify the function behavior
        mock_check_duplicate.assert_called_once_with(urls)

    @patch("indigobot.utils.etl.custom_loader.scrape_urls")
    @patch("indigobot.utils.etl.custom_loader.load_urls")
    @patch("indigobot.utils.etl.custom_loader.jf_loader")
    @patch("os.path.exists")
    @patch("shutil.rmtree")
    def test_start_loader_with_exception(
        self, mock_rmtree, mock_exists, mock_jf_loader, mock_load_urls, mock_scrape_urls
    ):
        """Test start_loader function when an exception occurs."""
        # Setup mocks
        mock_exists.return_value = True
        mock_scrape_urls.side_effect = Exception("Test exception")

        # Call the function and verify it raises the exception
        with self.assertRaises(Exception) as context:
            start_loader()

        # Verify the exception message
        self.assertIn("Test exception", str(context.exception))
        mock_exists.assert_not_called()  # Should not be called due to the exception
        mock_rmtree.assert_not_called()  # Should not be called due to the exception

    @patch("indigobot.utils.etl.custom_loader.crawl")
    @patch("indigobot.utils.etl.custom_loader.refine_text")
    @patch("indigobot.utils.etl.custom_loader.load_JSON_files")
    @patch("indigobot.utils.etl.custom_loader.load_docs")
    @patch("os.makedirs")
    def test_jf_loader_with_new_urls(
        self,
        mock_makedirs,
        mock_load_docs,
        mock_load_json,
        mock_refine_text,
        mock_crawl,
    ):
        """Test jf_loader function with new URLs."""
        # Setup mocks
        mock_crawl.return_value = True  # New URLs found
        mock_load_json.return_value = ["doc1", "doc2"]

        # Call the function
        jf_loader()

        # Verify the function behavior
        mock_crawl.assert_called_once()
        mock_refine_text.assert_called_once()
        mock_makedirs.assert_called_once()
        mock_load_json.assert_called_once()
        mock_load_docs.assert_called_once_with(["doc1", "doc2"])

    @patch("indigobot.utils.etl.custom_loader.crawl")
    def test_jf_loader_no_new_urls(self, mock_crawl):
        """Test jf_loader function with no new URLs."""
        # Setup mocks
        mock_crawl.return_value = False  # No new URLs

        # Call the function
        jf_loader()

        # Verify the function behavior
        mock_crawl.assert_called_once()

    @patch("indigobot.utils.etl.custom_loader.scrape_urls")
    @patch("indigobot.utils.etl.custom_loader.load_urls")
    @patch("indigobot.utils.etl.custom_loader.jf_loader")
    @patch("os.path.exists")
    @patch("shutil.rmtree")
    def test_start_loader(
        self, mock_rmtree, mock_exists, mock_jf_loader, mock_load_urls, mock_scrape_urls
    ):
        """Test start_loader function."""
        # Setup mocks
        mock_exists.return_value = False  # Change to False to avoid rmtree call

        # Call the function
        start_loader()

        # Verify the function behavior
        self.assertEqual(
            mock_scrape_urls.call_count, 2
        )  # Called for r_url_list and cls_url_list
        mock_load_urls.assert_called_once()
        mock_jf_loader.assert_called_once()
        mock_exists.assert_called_once_with(CRAWL_TEMP)
        mock_rmtree.assert_not_called()  # Should not be called when exists returns False


if __name__ == "__main__":
    unittest.main()
