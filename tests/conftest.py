"""
Pytest configuration file for IndigoBot tests.

This file contains fixtures and configuration for pytest to use when running tests.
"""

import pytest
from unittest.mock import MagicMock


@pytest.fixture
def mock_llm():
    """Create a mock language model for testing."""
    mock = MagicMock()
    mock.invoke.return_value = MagicMock(content="Test response")
    return mock


@pytest.fixture
def mock_vectorstore():
    """Create a mock vectorstore for testing."""
    mock = MagicMock()
    mock.add_texts = MagicMock()
    mock.as_retriever = MagicMock()
    return mock


@pytest.fixture
def mock_places_tool():
    """Create a mock PlacesLookupTool for testing."""
    mock = MagicMock()
    mock.lookup_place.return_value = "Test place info"
    return mock
