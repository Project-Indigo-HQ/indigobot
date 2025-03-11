"""
Pytest configuration file for IndigoBot tests.

This file contains fixtures and configuration for pytest to use when running tests.
"""

from unittest.mock import MagicMock

import pytest


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


@pytest.fixture
def mock_redis_client():
    """Create a mock Redis client for testing."""
    mock = MagicMock()
    mock.get.return_value = None
    mock.set.return_value = True
    return mock


@pytest.fixture
def mock_chatbot_app():
    """Create a mock chatbot app for testing."""
    mock = MagicMock()
    mock_message = MagicMock()
    mock_message.content = "Test response"
    mock.stream.return_value = [{"messages": [mock_message]}]
    return mock


@pytest.fixture
def mock_google_places_tool():
    """Create a mock GooglePlacesTool for testing."""
    mock = MagicMock()
    mock.run.return_value = {
        "name": "Test Place",
        "formatted_address": "123 Test St",
        "formatted_phone_number": "555-1234",
        "website": "https://test.com",
        "opening_hours": {"weekday_text": ["Monday: 9AM-5PM", "Tuesday: 9AM-5PM"]},
    }
    return mock
