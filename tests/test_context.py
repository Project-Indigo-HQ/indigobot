"""
Unit tests for the context module.

This module contains tests for the functions in the indigobot.context module.
"""

import unittest
from unittest.mock import MagicMock, patch

from indigobot.context import invoke_indybot


class TestContextModule(unittest.TestCase):
    """Test cases for the context module functions."""

    @patch("indigobot.context.chatbot_app")
    @patch("indigobot.context.get_cached_response")
    def test_invoke_indybot_success(self, mock_get_cached, mock_chatbot_app):
        """Test the invoke_indybot function with successful response."""
        # Setup
        mock_get_cached.return_value = None  # No cached response
        mock_message = MagicMock()
        mock_message.content = "This is a response"
        mock_chatbot_app.stream.return_value = [{"messages": [mock_message]}]

        # Execute
        result = invoke_indybot("Hello", {})

        # Assert
        self.assertEqual(result, "This is a response")
        mock_chatbot_app.stream.assert_called_once()

    @patch("indigobot.context.chatbot_app")
    @patch("indigobot.context.get_cached_response")
    def test_invoke_indybot_error(self, mock_get_cached, mock_chatbot_app):
        """Test the invoke_indybot function with an error."""
        # Setup
        mock_get_cached.return_value = None  # No cached response
        mock_chatbot_app.stream.side_effect = Exception("Test error")

        # Execute
        result = invoke_indybot("Hello", {})

        # Assert
        self.assertEqual(result, "It seems an error has occurred.")


if __name__ == "__main__":
    unittest.main()
