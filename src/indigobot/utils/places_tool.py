"""
This module provides tools for looking up place supplementary information using the Google Places API.
"""

import os
from datetime import datetime, time
from typing import Any, Dict

import pytz
from langchain_core.tools import StructuredTool
from langchain_google_community import GooglePlacesTool
from pydantic import BaseModel, Field

from indigobot.config import llm, vectorstore


class PlacesLookupTool:
    """A tool for retrieving and formatting place information from Google Places API."""

    def __init__(self):
        """Initialize the Places tool with API key and base configuration."""
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
        """Convert time string from '0000' format to datetime.time object.

        :param time_str: Time string in '0000' format (HHMM)
        :type time_str: str
        :return: Converted time object
        :rtype: datetime.time
        """
        return time(int(time_str[:2]), int(time_str[2:]))

    def _format_time(self, t: time) -> str:
        """Convert time object to '00:00' format.

        :param t: Time object to format
        :type t: datetime.time
        :return: Formatted time string in HH:MM format
        :rtype: str
        """
        return t.strftime("%H:%M")

    def _get_current_status(self, place_data: Dict[str, Any]) -> str:
        """Determine if a place is currently open and when it will close/open.

        :param place_data: Dictionary containing place data from Google Places API
        :type place_data: Dict[str, Any]
        :return: String describing current status (e.g., "Open (Closes at 17:00)")
        :rtype: str
        """
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
        """Format the hours section of place details.

        :param place_data: Dictionary containing place data from Google Places API
        :type place_data: Dict[str, Any]
        :return: Formatted string with opening hours information
        :rtype: str
        """
        sections = []

        weekday_text = place_data.get("opening_hours", {}).get("weekday_text", [])
        if weekday_text:
            sections.append("Opening Hours:")
            sections.extend(f"  {hour}" for hour in weekday_text)
            return "\n".join(sections)

        return "Hours: Not available"

    def _format_place_details(self, place_data: Dict[str, Any]) -> str:
        """Format place details into a readable string.

        :param place_data: Dictionary containing place data from Google Places API
        :type place_data: Dict[str, Any]
        :return: Formatted string with all place details
        :rtype: str
        """
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
        """Look up details for a place using Google Places API.

        :param query: The search query for the place (e.g., "Portland Library")
        :type query: str
        :return: Formatted string with place details including hours and current status
        :rtype: str
        :raises Exception: If there's an error fetching place details
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


class LookupPlacesInput(BaseModel):
    """Pydantic model for validating input to the lookup_place_info function.

    :ivar user_input: User's original prompt to be processed by the lookup_place() function
    :vartype user_input: str
    """

    user_input: str = Field(
        ...,
        description="User's original prompt to be processed by the lookup_place() function",
    )


def extract_place_name(place_input):
    """Extract potential place name from user query or model response.

    :param place_input: The text from which to extract a place name
    :type place_input: str
    :return: The language model response containing the extracted place name,
             or None if no place name is found
    :rtype: object
    """

    extraction_prompt = f"""
    Extract the name of the place that the user is asking about from this conversation.
    Return just the name of the place without any explanation.
    If no specific place name is mentioned, return 'NONE'. 
    User question: {place_input}
    """

    potential_name = llm.invoke(extraction_prompt)

    if potential_name == "NONE":
        return None

    return potential_name


def store_place_info_in_vectorstore(place_name: str, place_info: str) -> None:
    """Store the place information in the vectorstore for future retrieval.

    :param place_name: The name of the place
    :type place_name: str
    :param place_info: The information about the place to store
    :type place_info: str
    :return: None
    """
    document_text = f"""Information about {place_name}: {place_info}"""
    vectorstore.add_texts(
        texts=[document_text],
        metadatas=[{"source": "google_places_api", "place_name": place_name}],
    )


def create_place_info_response(original_answer: str, place_info: str) -> str:
    """Create a new response incorporating the place information.

    :param original_answer: The initial response before place information was retrieved
    :type original_answer: str
    :param place_info: The information about the place retrieved from the API
    :type place_info: str
    :return: A new response incorporating the place information
    :rtype: str
    """

    response_prompt = f"""
    The user asked about a place, and our initial response was: "{original_answer}".
    We've now found this information from Google Places API: {place_info}.
    Create a helpful response that provides the accurate information we found
    and is limited to one sentence. If you don't have the info originally 
    asked for, be sure to mention as much.
    """

    new_response = llm.invoke(response_prompt)

    return new_response.content


def lookup_place_info(user_input: str) -> str:
    """Look up place information using the Google Places API, load into store, and integrate it into the chat.

    :param user_input: The user's query containing a potential place name
    :type user_input: str
    :return: A response incorporating the place information
    :rtype: str
    :raises Exception: If there's an error extracting the place name
    """
    try:
        place_name = extract_place_name(user_input)
    except Exception as e:
        print(f"Error in extract_place_name: {e}")

    plt = PlacesLookupTool()
    place_info = plt.lookup_place(place_name.content)

    store_place_info_in_vectorstore(place_name.content, place_info)

    improved_answer = create_place_info_response(user_input, place_info)
    return improved_answer


lookup_place_tool = StructuredTool.from_function(
    func=lookup_place_info,
    name="lookup_place_tool",
    description="Use this tool to fill in missing prompt/query knowledge with a Google Places API call.",
    return_direct=True,
    args_schema=LookupPlacesInput,
)
