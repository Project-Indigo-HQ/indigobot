"""
Extended tests for the quick_api module.
"""

import json
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException, Request
from fastapi.testclient import TestClient
from slowapi.errors import RateLimitExceeded

from indigobot.quick_api import (
    app,
    get_conversation_id,
    limiter,
    ratelimit_handler,
    send_message_to_chatwoot,
    webhook,
)


class TestQuickApiExtended(unittest.TestCase):
    """Extended test cases for the quick_api module."""

    def setUp(self):
        self.client = TestClient(app)

    @patch("indigobot.quick_api.json.loads")
    def test_get_conversation_id(self, mock_loads):
        """Test get_conversation_id function with valid payload."""
        # Set up mock
        mock_loads.return_value = {"id": "12345"}

        # Create a mock request with a conversation ID
        mock_request = MagicMock()
        mock_request.body = b'{"id": "12345"}'

        # Call the function
        result = get_conversation_id(mock_request)

        # Check the result
        self.assertEqual(result, "12345")

    @patch("indigobot.quick_api.json.loads")
    def test_get_conversation_id_missing(self, mock_loads):
        """Test get_conversation_id function with missing ID."""
        # Set up mock
        mock_loads.return_value = {"other_field": "value"}

        # Create a mock request with no ID
        mock_request = MagicMock()
        mock_request.body = b'{"other_field": "value"}'

        # Call the function
        result = get_conversation_id(mock_request)

        # Check the result
        self.assertEqual(result, "unknown")

    @patch("indigobot.quick_api.json.loads")
    def test_get_conversation_id_error(self, mock_loads):
        """Test get_conversation_id function with invalid JSON."""
        # Set up mock to raise an exception
        mock_loads.side_effect = Exception("Invalid JSON")

        # Create a mock request with invalid JSON
        mock_request = MagicMock()
        mock_request.body = b"invalid json"

        # Call the function
        result = get_conversation_id(mock_request)

        # Check the result
        self.assertEqual(result, "unknown")

    @patch("indigobot.quick_api.requests.post")
    def test_send_message_to_chatwoot_success(self, mock_post):
        """Test send_message_to_chatwoot function with successful response."""
        # Set up mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        # Call the function
        send_message_to_chatwoot("12345", "Test message")

        # Check that requests.post was called with correct parameters
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        self.assertIn("json", kwargs)
        self.assertEqual(kwargs["json"]["content"], "Test message")
        self.assertEqual(kwargs["json"]["message_type"], "outgoing")

    @patch("indigobot.quick_api.requests.post")
    def test_send_message_to_chatwoot_error(self, mock_post):
        """Test send_message_to_chatwoot function with error response."""
        # Set up mock to raise an exception
        mock_post.side_effect = Exception("Test error")

        # We need to patch the environment variables
        with patch.dict(
            "os.environ",
            {
                "CHATWOOT_ACCESS_TOKEN": "test-token",
                "CHATWOOT_ACCOUNT_ID": "123",
                "CHATWOOT_API_URL": "https://test-url.com",
            },
        ):
            # The function doesn't handle exceptions internally, so we need to catch it
            with self.assertRaises(Exception) as context:
                send_message_to_chatwoot("12345", "Test message")

            # Check that the exception was raised
            self.assertEqual(str(context.exception), "Test error")

            # Check that requests.post was called
            mock_post.assert_called_once()

    @patch("indigobot.quick_api.invoke_indybot")
    def test_webhook_valid_payload(self, mock_invoke):
        """Test webhook endpoint with valid payload."""
        # Set up mock
        mock_invoke.return_value = "Test response"

        # Create test payload
        payload = {
            "id": "12345",
            "messages": [{"content": "Test question", "conversation_id": "12345"}],
        }

        # Use the TestClient to make a request
        response = self.client.post(
            "/webhook", json=payload, headers={"Authorization": "valid-token"}
        )

        # Check the response
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["answer"], "Test response")
        mock_invoke.assert_called_once()

    @patch("indigobot.quick_api.invoke_indybot")
    def test_webhook_empty_content(self, mock_invoke):
        """Test webhook endpoint with empty message content."""
        # Create test payload with empty content
        payload = {
            "id": "12345",
            "messages": [{"content": "", "conversation_id": "12345"}],
        }

        # Use the TestClient to make a request
        response = self.client.post(
            "/webhook", json=payload, headers={"Authorization": "valid-token"}
        )

        # Check the response - the API returns 500 for empty content
        self.assertEqual(response.status_code, 500)
        mock_invoke.assert_not_called()

    @patch("indigobot.quick_api.invoke_indybot")
    def test_webhook_exception(self, mock_invoke):
        """Test webhook endpoint with exception during processing."""
        # Set up mock to raise an exception
        mock_invoke.side_effect = Exception("Test error")

        # Create test payload
        payload = {
            "id": "12345",
            "messages": [{"content": "Test question", "conversation_id": "12345"}],
        }

        # Use the TestClient to make a request
        response = self.client.post(
            "/webhook", json=payload, headers={"Authorization": "valid-token"}
        )

        # Check the response
        self.assertEqual(response.status_code, 500)
        mock_invoke.assert_called_once()

    def test_ratelimit_handler(self):
        """Test rate limit exception handler."""
        # Create mock request and exception
        mock_request = MagicMock()

        # Create a proper RateLimitExceeded exception with required attributes
        mock_exc = MagicMock(spec=RateLimitExceeded)
        mock_exc.detail = "Test rate limit exceeded"

        # Call the handler (use asyncio.run to handle the coroutine)
        import asyncio

        response = asyncio.run(ratelimit_handler(mock_request, mock_exc))

        # Check response
        self.assertEqual(response.status_code, 429)
        self.assertIn("Rate limit exceeded", response.body.decode())

    def test_root_endpoint(self):
        """Test the root endpoint."""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "healthy")
        self.assertEqual(data["version"], "1.0.0")
