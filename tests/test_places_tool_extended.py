"""
Extended tests for the places_tool module.
"""

import unittest
from datetime import datetime, time
from unittest.mock import MagicMock, patch

import pytz

from indigobot.utils.places_tool import (
    PlacesLookupTool,
    create_place_info_response,
    extract_place_name,
    lookup_place_info,
    store_place_info_in_vectorstore,
)


class TestPlacesToolExtended(unittest.TestCase):
    """Extended test cases for the places_tool module."""

    def setUp(self):
        self.places_tool = PlacesLookupTool()

        # Sample place data for testing
        self.sample_place_data = {
            "name": "Test Place",
            "formatted_address": "123 Test St, Portland, OR 97201",
            "formatted_phone_number": "(503) 555-1234",
            "website": "https://testplace.com",
            "opening_hours": {
                "open_now": True,
                "periods": [
                    {
                        "open": {"day": 0, "time": "0800"},
                        "close": {"day": 0, "time": "1700"},
                    },
                    {
                        "open": {"day": 1, "time": "0800"},
                        "close": {"day": 1, "time": "1700"},
                    },
                ],
                "weekday_text": [
                    "Monday: 8:00 AM – 5:00 PM",
                    "Tuesday: 8:00 AM – 5:00 PM",
                ],
            },
        }

    def test_parse_time(self):
        """Test _parse_time method."""
        result = self.places_tool._parse_time("0830")
        self.assertEqual(result, time(8, 30))

        result = self.places_tool._parse_time("1745")
        self.assertEqual(result, time(17, 45))

    def test_format_time(self):
        """Test _format_time method."""
        result = self.places_tool._format_time(time(8, 30))
        self.assertEqual(result, "08:30")

        result = self.places_tool._format_time(time(17, 45))
        self.assertEqual(result, "17:45")

    @patch("indigobot.utils.places_tool.datetime")
    def test_get_current_status_open(self, mock_datetime):
        """Test _get_current_status method when place is open."""
        # Mock current time to be during opening hours (Monday at 12:00)
        mock_now = MagicMock()
        mock_now.weekday.return_value = 0  # Monday
        mock_now.time.return_value = time(12, 0)
        mock_datetime.now.return_value = mock_now

        # Call the method
        result = self.places_tool._get_current_status(self.sample_place_data)

        # Check the result
        self.assertIn("Open", result)
        self.assertIn("Closes at 17:00", result)

    @patch("indigobot.utils.places_tool.datetime")
    def test_get_current_status_closed(self, mock_datetime):
        """Test _get_current_status method when place is closed."""
        # Mock current time to be outside opening hours (Monday at 18:00)
        mock_now = MagicMock()
        mock_now.weekday.return_value = 0  # Monday
        mock_now.time.return_value = time(18, 0)
        mock_datetime.now.return_value = mock_now

        # Call the method
        result = self.places_tool._get_current_status(self.sample_place_data)

        # Check the result
        self.assertEqual(result, "Closed")

    def test_format_hours_section(self):
        """Test _format_hours_section method."""
        # Call the method
        result = self.places_tool._format_hours_section(self.sample_place_data)

        # Check the result
        self.assertIn("Opening Hours:", result)
        self.assertIn("Monday: 8:00 AM – 5:00 PM", result)
        self.assertIn("Tuesday: 8:00 AM – 5:00 PM", result)

    def test_format_place_details(self):
        """Test _format_place_details method."""
        # Call the method
        result = self.places_tool._format_place_details(self.sample_place_data)

        # Check the result
        self.assertIn("Name: Test Place", result)
        self.assertIn("Address: 123 Test St, Portland, OR 97201", result)
        self.assertIn("Phone Number: (503) 555-1234", result)
        self.assertIn("Website: https://testplace.com", result)
        self.assertIn("Current Status:", result)
        self.assertIn("Opening Hours:", result)

    @patch("indigobot.utils.places_tool.PlacesLookupTool._get_current_status")
    def test_format_place_details_missing_fields(self, mock_get_status):
        """Test _format_place_details method with missing fields."""
        # Set up mock
        mock_get_status.return_value = "Open"

        # Create place data with missing fields
        place_data = {
            "name": "Test Place",
            "formatted_address": "123 Test St, Portland, OR 97201",
        }

        # Call the method
        result = self.places_tool._format_place_details(place_data)

        # Check the result
        self.assertIn("Name: Test Place", result)
        self.assertIn("Address: 123 Test St, Portland, OR 97201", result)
        self.assertNotIn("Phone Number:", result)
        self.assertNotIn("Website:", result)

    @patch("indigobot.utils.places_tool.GooglePlacesTool")
    def test_lookup_place_success(self, mock_google_places_tool):
        """Test lookup_place method with successful response."""
        # Set up mock
        mock_tool_instance = MagicMock()
        mock_tool_instance.run.return_value = self.sample_place_data
        self.places_tool.places_tool = mock_tool_instance

        # Call the method
        result = self.places_tool.lookup_place("Test Place")

        # Check the result
        self.assertIn("Name: Test Place", result)
        self.assertIn("Address: 123 Test St, Portland, OR 97201", result)
        mock_tool_instance.run.assert_called_once_with("Test Place")

    @patch("indigobot.utils.places_tool.GooglePlacesTool")
    def test_lookup_place_error(self, mock_google_places_tool):
        """Test lookup_place method with error response."""
        # Set up mock to raise an exception
        mock_tool_instance = MagicMock()
        mock_tool_instance.run.side_effect = Exception("Test error")
        self.places_tool.places_tool = mock_tool_instance

        # Call the method
        result = self.places_tool.lookup_place("Test Place")

        # Check the result
        self.assertIn("Error fetching place details", result)
        mock_tool_instance.run.assert_called_once_with("Test Place")

    @patch("indigobot.utils.places_tool.llm")
    def test_extract_place_name(self, mock_llm):
        """Test extract_place_name function."""
        # Set up mock
        mock_response = MagicMock()
        mock_response.content = "Portland Rescue Mission"
        mock_llm.invoke.return_value = mock_response

        # Call the function
        result = extract_place_name("Where is the Portland Rescue Mission?")

        # Check the result
        self.assertEqual(result, mock_response)
        mock_llm.invoke.assert_called_once()

    @patch("indigobot.utils.places_tool.vectorstore")
    def test_store_place_info_in_vectorstore(self, mock_vectorstore):
        """Test store_place_info_in_vectorstore function."""
        # Call the function
        store_place_info_in_vectorstore("Test Place", "Test place information")

        # Check that add_texts was called with correct parameters
        mock_vectorstore.add_texts.assert_called_once()
        kwargs = mock_vectorstore.add_texts.call_args.kwargs
        texts = kwargs.get("texts", [])
        metadatas = kwargs.get("metadatas", [])

        self.assertEqual(
            texts[0], "Information about Test Place: Test place information"
        )
        self.assertEqual(metadatas[0]["source"], "google_places_api")
        self.assertEqual(metadatas[0]["place_name"], "Test Place")

    @patch("indigobot.utils.places_tool.llm")
    def test_create_place_info_response(self, mock_llm):
        """Test create_place_info_response function."""
        # Set up mock
        mock_response = MagicMock()
        mock_response.content = "The Portland Rescue Mission is located at 123 Main St."
        mock_llm.invoke.return_value = mock_response

        # Call the function
        result = create_place_info_response(
            "I don't know where the Portland Rescue Mission is.",
            "Portland Rescue Mission is at 123 Main St.",
        )

        # Check the result
        self.assertEqual(
            result, "The Portland Rescue Mission is located at 123 Main St."
        )
        mock_llm.invoke.assert_called_once()

    @patch("indigobot.utils.places_tool.create_place_info_response")
    @patch("indigobot.utils.places_tool.store_place_info_in_vectorstore")
    @patch("indigobot.utils.places_tool.extract_place_name")
    @patch("indigobot.utils.places_tool.PlacesLookupTool")
    def test_lookup_place_info(
        self, mock_plt_class, mock_extract, mock_store, mock_create
    ):
        """Test lookup_place_info function."""
        # Set up mocks
        mock_place_name = MagicMock()
        mock_place_name.content = "Portland Rescue Mission"
        mock_extract.return_value = mock_place_name

        mock_plt_instance = MagicMock()
        mock_plt_instance.lookup_place.return_value = "Place details"
        mock_plt_class.return_value = mock_plt_instance

        mock_create.return_value = "Final response"

        # Call the function
        result = lookup_place_info("Where is the Portland Rescue Mission?")

        # Check the result
        self.assertEqual(result, "Final response")
        mock_extract.assert_called_once()
        mock_plt_instance.lookup_place.assert_called_once_with(
            "Portland Rescue Mission"
        )
        mock_store.assert_called_once()
        mock_create.assert_called_once()
