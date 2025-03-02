"""
Unit tests for the places_tool module.

This module contains tests for the PlacesLookupTool class and its methods
for retrieving and formatting place information.
"""

import unittest
from unittest.mock import patch, MagicMock
from datetime import time, datetime

import pytz

from indigobot.places_tool import PlacesLookupTool


class TestPlacesLookupTool(unittest.TestCase):
    """Test cases for the PlacesLookupTool class."""

    def setUp(self):
        """Set up test fixtures."""
        self.tool = PlacesLookupTool()

    def test_parse_time(self):
        """Test the _parse_time method."""
        # Test regular time
        result = self.tool._parse_time("1430")
        self.assertEqual(result, time(14, 30))
        
        # Test midnight
        result = self.tool._parse_time("0000")
        self.assertEqual(result, time(0, 0))
        
        # Test noon
        result = self.tool._parse_time("1200")
        self.assertEqual(result, time(12, 0))

    def test_format_time(self):
        """Test the _format_time method."""
        # Test regular time
        result = self.tool._format_time(time(14, 30))
        self.assertEqual(result, "14:30")
        
        # Test midnight
        result = self.tool._format_time(time(0, 0))
        self.assertEqual(result, "00:00")
        
        # Test noon
        result = self.tool._format_time(time(12, 0))
        self.assertEqual(result, "12:00")

    @patch("indigobot.places_tool.datetime")
    def test_get_current_status_open(self, mock_datetime):
        """Test the _get_current_status method when place is open."""
        # Setup - Monday at 10:30 AM
        mock_now = MagicMock()
        mock_now.weekday.return_value = 0  # Monday
        mock_now.time.return_value = time(10, 30)
        mock_datetime.now.return_value = mock_now
        
        place_data = {
            "opening_hours": {
                "periods": [
                    {
                        "open": {"day": 0, "time": "0900"},
                        "close": {"day": 0, "time": "1700"}
                    }
                ]
            }
        }
        
        # Execute
        result = self.tool._get_current_status(place_data)
        
        # Assert
        self.assertEqual(result, "Open (Closes at 17:00)")

    @patch("indigobot.places_tool.datetime")
    def test_get_current_status_closed(self, mock_datetime):
        """Test the _get_current_status method when place is closed."""
        # Setup - Monday at 8:30 AM (before opening)
        mock_now = MagicMock()
        mock_now.weekday.return_value = 0  # Monday
        mock_now.time.return_value = time(8, 30)
        mock_datetime.now.return_value = mock_now
        
        place_data = {
            "opening_hours": {
                "periods": [
                    {
                        "open": {"day": 0, "time": "0900"},
                        "close": {"day": 0, "time": "1700"}
                    }
                ]
            }
        }
        
        # Execute
        result = self.tool._get_current_status(place_data)
        
        # Assert
        self.assertEqual(result, "Closed (Opens at 09:00)")

    def test_format_hours_section(self):
        """Test the _format_hours_section method."""
        # Setup
        place_data = {
            "opening_hours": {
                "weekday_text": [
                    "Monday: 9:00 AM – 5:00 PM",
                    "Tuesday: 9:00 AM – 5:00 PM",
                    "Wednesday: 9:00 AM – 5:00 PM"
                ]
            }
        }
        
        # Execute
        result = self.tool._format_hours_section(place_data)
        
        # Assert
        expected = "Opening Hours:\n  Monday: 9:00 AM – 5:00 PM\n  Tuesday: 9:00 AM – 5:00 PM\n  Wednesday: 9:00 AM – 5:00 PM"
        self.assertEqual(result, expected)
        
        # Test with no hours
        result = self.tool._format_hours_section({})
        self.assertEqual(result, "Hours: Not available")

    def test_format_place_details(self):
        """Test the _format_place_details method."""
        # Setup
        place_data = {
            "name": "Portland Library",
            "formatted_address": "123 Main St, Portland, OR",
            "formatted_phone_number": "555-123-4567",
            "website": "https://library.portland.gov",
            "opening_hours": {
                "weekday_text": [
                    "Monday: 9:00 AM – 5:00 PM",
                    "Tuesday: 9:00 AM – 5:00 PM"
                ]
            }
        }
        
        # Mock the _get_current_status method
        self.tool._get_current_status = MagicMock(return_value="Open (Closes at 17:00)")
        
        # Execute
        result = self.tool._format_place_details(place_data)
        
        # Assert
        self.assertIn("Name: Portland Library", result)
        self.assertIn("Address: 123 Main St, Portland, OR", result)
        self.assertIn("Phone Number: 555-123-4567", result)
        self.assertIn("Website: https://library.portland.gov", result)
        self.assertIn("Current Status: Open (Closes at 17:00)", result)
        self.assertIn("Opening Hours:", result)

    @patch("indigobot.places_tool.GooglePlacesTool")
    def test_lookup_place_success(self, mock_google_places):
        """Test the lookup_place method with successful response."""
        # Setup
        mock_instance = MagicMock()
        mock_google_places.return_value = mock_instance
        
        place_data = {
            "name": "Portland Library",
            "formatted_address": "123 Main St, Portland, OR"
        }
        mock_instance.run.return_value = place_data
        
        # Replace the actual places_tool with our mock
        self.tool.places_tool = mock_instance
        
        # Mock the _format_place_details method
        self.tool._format_place_details = MagicMock(return_value="Formatted place details")
        
        # Execute
        result = self.tool.lookup_place("Portland Library")
        
        # Assert
        self.assertEqual(result, "Formatted place details")
        mock_instance.run.assert_called_once_with("Portland Library")
        self.tool._format_place_details.assert_called_once_with(place_data)

    @patch("indigobot.places_tool.GooglePlacesTool")
    def test_lookup_place_error(self, mock_google_places):
        """Test the lookup_place method with error response."""
        # Setup
        mock_instance = MagicMock()
        mock_google_places.return_value = mock_instance
        mock_instance.run.side_effect = Exception("API error")
        
        # Replace the actual places_tool with our mock
        self.tool.places_tool = mock_instance
        
        # Execute
        result = self.tool.lookup_place("Portland Library")
        
        # Assert
        self.assertEqual(result, "Error fetching place details: API error")


if __name__ == "__main__":
    unittest.main()
