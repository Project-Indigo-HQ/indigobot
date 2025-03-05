"""
Unit tests for the context module.

This module contains tests for the functions in the indigobot.context module,
including place name extraction, place info storage, and response creation.
"""

import unittest
from unittest.mock import MagicMock, patch

from indigobot.context import (
    create_place_info_response,
    extract_place_name,
    invoke_indybot,
    lookup_place_info,
    store_place_info_in_vectorstore,
)


class TestContextModule(unittest.TestCase):
    """Test cases for the context module functions."""

    @patch("indigobot.context.llm")
    def test_extract_place_name(self, mock_llm):
        """Test the extract_place_name function."""
        # Setup
        mock_llm.invoke.return_value = MagicMock(content="Portland Library")

        # Execute
        result = extract_place_name("Where is the Portland Library located?")

        # Assert
        self.assertEqual(result.content, "Portland Library")
        mock_llm.invoke.assert_called_once()

        # Test with no place name
        mock_llm.invoke.reset_mock()
        mock_llm.invoke.return_value = "NONE"
        result = extract_place_name("What time is it?")
        self.assertIsNone(result)

    @patch("indigobot.context.vectorstore")
    def test_store_place_info_in_vectorstore(self, mock_vectorstore):
        """Test the store_place_info_in_vectorstore function."""
        # Setup
        place_name = "Portland Library"
        place_info = "123 Main St, Portland, OR"

        # Execute
        store_place_info_in_vectorstore(place_name, place_info)

        # Assert
        mock_vectorstore.add_texts.assert_called_once_with(
            texts=[f"Information about {place_name}: {place_info}"],
            metadatas=[{"source": "google_places_api", "place_name": place_name}],
        )

    @patch("indigobot.context.llm")
    def test_create_place_info_response(self, mock_llm):
        """Test the create_place_info_response function."""
        # Setup
        mock_response = MagicMock()
        mock_response.content = (
            "The Portland Library is located at 123 Main St and is open until 5pm."
        )
        mock_llm.invoke.return_value = mock_response

        original_answer = "I'm not sure about the Portland Library."
        place_info = "Address: 123 Main St, Portland, OR\nHours: 9am-5pm"

        # Execute
        result = create_place_info_response(original_answer, place_info)

        # Assert
        self.assertEqual(result, mock_response.content)
        mock_llm.invoke.assert_called_once()

    @patch("indigobot.context.chatbot_app")
    def test_invoke_indybot(self, mock_chatbot_app):
        """Test the invoke_indybot function."""
        # Setup
        mock_message = MagicMock()
        mock_message.content = "This is a response"
        mock_chatbot_app.stream.return_value = [{"messages": [mock_message]}]

        # Execute
        result = invoke_indybot("Hello", {})

        # Assert
        self.assertEqual(result, "This is a response")
        mock_chatbot_app.stream.assert_called_once()

        # Test exception handling
        mock_chatbot_app.stream.side_effect = Exception("Test error")
        result = invoke_indybot("Hello", {})
        self.assertEqual(result, "Error invoking indybot: Test error")

    @patch("indigobot.context.extract_place_name")
    @patch("indigobot.context.PlacesLookupTool")
    @patch("indigobot.context.create_place_info_response")
    def test_lookup_place_info(
        self, mock_create_response, mock_places_tool, mock_extract_name
    ):
        """Test the lookup_place_info function."""
        # Setup
        mock_name = MagicMock()
        mock_name.content = "Portland Library"
        mock_extract_name.return_value = mock_name

        mock_tool_instance = MagicMock()
        mock_places_tool.return_value = mock_tool_instance
        mock_tool_instance.lookup_place.return_value = "Library info"

        mock_create_response.return_value = "The Portland Library is at 123 Main St."

        # Execute
        result = lookup_place_info("Where is the Portland Library?")

        # Assert
        self.assertEqual(result, "The Portland Library is at 123 Main St.")
        mock_extract_name.assert_called_once()
        mock_places_tool.assert_called_once()
        mock_tool_instance.lookup_place.assert_called_once_with("Portland Library")
        mock_create_response.assert_called_once()


if __name__ == "__main__":
    unittest.main()
