import os
from datetime import datetime, time
from typing import Any, Dict

import pytz
from langchain_google_community import GooglePlacesTool


class PlacesLookupTool:
    def __init__(self):
        """Initialize the Places tool with API key and base configuration"""
        self.api_key = os.getenv("GPLACES_API_KEY")
        self.places_tool = GooglePlacesTool(
            gplaces_api_key=self.api_key,
            fields=[
                "formatted_address",
                "name",
                "opening_hours",
                "opening_hours/open_now",
                "opening_hours/periods",
                "opening_hours/weekday_text",
                "website",
                "formatted_phone_number",
                "business_status",
                "utc_offset",
            ],
            params={
                "type": "address",
                "language": "en",
                "region": "us",
            },
        )

    def _parse_time(self, time_str: str) -> time:
        """Convert time string from '0000' format to datetime.time object"""
        return time(int(time_str[:2]), int(time_str[2:]))

    def _format_time(self, t: time) -> str:
        """Convert time object to '00:00' format"""
        return t.strftime("%H:%M")

    def _get_current_status(self, place_data: Dict[str, Any]) -> str:
        """Determine if a place is currently open and when it will close/open"""
        try:
            pacific = pytz.timezone("America/Los_Angeles")
            now = datetime.now(pacific)
            current_day = now.weekday()
            current_time = now.time()

            periods = place_data.get("opening_hours", {}).get("periods", [])
            if not periods:
                open_now = place_data.get("opening_hours", {}).get("open_now")
                return (
                    "Open"
                    if open_now
                    else "Closed" if open_now is not None else "Hours unknown"
                )

            for period in periods:
                open_info = period.get("open", {})
                close_info = period.get("close", {})

                if not (open_info and close_info):
                    continue

                open_day = open_info.get("day")
                close_day = close_info.get("day")
                open_time = self._parse_time(open_info.get("time", "0000"))
                close_time = self._parse_time(close_info.get("time", "0000"))

                if open_day == current_day:
                    if open_time <= current_time < close_time:
                        return f"Open (Closes at {self._format_time(close_time)})"
                    elif current_time < open_time:
                        return f"Closed (Opens at {self._format_time(open_time)})"

                if close_day == (current_day + 1) % 7 and open_day == current_day:
                    if current_time >= open_time:
                        return (
                            f"Open (Closes tomorrow at {self._format_time(close_time)})"
                        )

                if open_day == (current_day - 1) % 7 and close_day == current_day:
                    if current_time < close_time:
                        return f"Open (Closes at {self._format_time(close_time)})"

            return "Closed"

        except Exception as e:
            return f"Hours unknown (Error: {str(e)})"

    def _format_hours_section(self, place_data: Dict[str, Any]) -> str:
        """Format the hours section of place details"""
        sections = []

        weekday_text = place_data.get("opening_hours", {}).get("weekday_text", [])
        if weekday_text:
            sections.append("Opening Hours:")
            sections.extend(f"  {hour}" for hour in weekday_text)
            return "\n".join(sections)

        return "Hours: Not available"

    def _format_place_details(self, place_data: Dict[str, Any]) -> str:
        """Format place details into a readable string"""
        sections = []

        name = place_data.get("name", "N/A")
        address = place_data.get("formatted_address", "N/A")
        sections.append(f"Name: {name}")
        sections.append(f"Address: {address}")

        phone = place_data.get("formatted_phone_number")
        if phone:
            sections.append(f"Phone Number: {phone}")

        website = place_data.get("website")
        if website:
            sections.append(f"Website: {website}")

        current_status = self._get_current_status(place_data)
        if current_status:
            sections.append(f"Current Status: {current_status}")

        hours_section = self._format_hours_section(place_data)
        if hours_section:
            sections.append(hours_section)

        return "\n".join(sections)

    def lookup_place(self, query: str) -> str:
        """
        Look up details for a place using Google Places API.

        Args:
            query: The search query for the place

        Returns:
            Formatted string with place details including hours and current status
        """

        try:
            result = self.places_tool.run(query)

            if isinstance(result, str):
                if result.startswith(("Error:", "1.")):
                    lines = result.split("\n")
                    place_id = next(
                        (
                            line.split("Google place ID: ")[1]
                            for line in lines
                            if "Google place ID:" in line
                        ),
                        None,
                    )

                    place_data = {
                        "name": (
                            lines[0].split(". ", 1)[1]
                            if ". " in lines[0]
                            else lines[0].replace("Error: ", "")
                        ),
                        "formatted_address": next(
                            (
                                line.split("Address: ", 1)[1]
                                for line in lines
                                if "Address:" in line
                            ),
                            "N/A",
                        ),
                        "formatted_phone_number": next(
                            (
                                line.split("Phone: ", 1)[1]
                                for line in lines
                                if "Phone:" in line and "Unknown" not in line
                            ),
                            None,
                        ),
                        "website": next(
                            (
                                line.split("Website: ", 1)[1]
                                for line in lines
                                if "Website:" in line and "Unknown" not in line
                            ),
                            None,
                        ),
                    }
                    return self._format_place_details(place_data)
                return f"Error: {result}"

            if isinstance(result, list):
                if not result:
                    return "No results found."
                result = result[0]

            return self._format_place_details(result)

        except Exception as e:
            return f"Error fetching place details: {str(e)}"
