"""
This is the main chatbot program/file for conversational capabilities and info distribution.
"""
import os
import readline  # Required for using arrow keys in CLI
import threading
from typing import Optional, Dict, Any

from langchain_google_community import GooglePlacesTool
from indigobot.context import chatbot_app
from indigobot.quick_api import start_api
from indigobot.utils.custom_loader import start_loader

# Initialize Google Places Tool
api_key = os.getenv("GPLACES_API_KEY")
places_tool = GooglePlacesTool(
    gplaces_api_key=api_key,
    fields=[
        "formatted_address",
        "name",
        "opening_hours",
        "open_now",
        "website",
        "formatted_phone_number",
        "business_status"
    ]
)

def format_place_details(place_data: Dict[str, Any]) -> str:
    """Format place details into a readable string."""
    sections = []
    
    # Name and address are required
    name = place_data.get('name', 'N/A')
    address = place_data.get('formatted_address', 'N/A')
    sections.append(f"Name: {name}")
    sections.append(f"Address: {address}")
    
    # Optional fields
    phone = place_data.get('formatted_phone_number')
    if phone:
        sections.append(f"Phone Number: {phone}")
        
    website = place_data.get('website')
    if website:
        sections.append(f"Website: {website}")
        
    # Handle opening hours if available
    opening_hours = place_data.get('opening_hours', {}).get('weekday_text', [])
    if opening_hours:
        sections.append("Opening Hours:")
        sections.extend(f"  {hour}" for hour in opening_hours)
        
    # Handle open now status if available
    open_now = place_data.get('open_now')
    if open_now is not None:
        sections.append(f"Currently Open: {'Yes' if open_now else 'No'}")
        
    return "\n".join(sections)

def fetch_place_details(query: str) -> Optional[str]:
    """Fetch details for a place using Google Places API."""
    if not query.strip():
        return None
        
    try:
        result = places_tool.run(query)
        
        # Handle string results (including error messages)
        if isinstance(result, str):
            if result.startswith(('Error:', '1.')):
                lines = result.split('\n')
                place_data = {
                    'name': lines[0].split('. ', 1)[1] if '. ' in lines[0] else lines[0].replace('Error: ', ''),
                    'formatted_address': next((line.split('Address: ', 1)[1] for line in lines if 'Address:' in line), 'N/A'),
                    'formatted_phone_number': next((line.split('Phone: ', 1)[1] for line in lines if 'Phone:' in line and 'Unknown' not in line), None),
                    'website': next((line.split('Website: ', 1)[1] for line in lines if 'Website:' in line and 'Unknown' not in line), None)
                }
                return format_place_details(place_data)
            return f"Error: {result}"
            
        # Handle list results
        if isinstance(result, list):
            if not result:
                return "No results found."
            result = result[0]
            
        return format_place_details(result)

    except Exception as e:
        return f"Error fetching place details: {str(e)}"

def load():
    """
    Prompt user to execute the document loader functionality.

    Asks the user if they want to run the document loader and executes it if confirmed.
    Uses the start_loader() function from custom_loader module.

    :raises: Exception if the loader encounters an error
    """
    load_res = input("Would you like to execute the loader? (y/n) ")
    if load_res == "y":
        try:
            start_loader()
        except Exception as e:
            print(f"Error booting loader: {e}")


def api():
    """
    Prompt user to start the API server.

    Asks the user if they want to enable the API server and starts it if confirmed.
    Launches quick_api.py as a subprocess and waits 10 seconds for initialization.

    :raises: Exception if the API server fails to start
    """
    load_res = input("Would you like to enable the API? (y/n) ")
    if load_res == "y":
        try:
            api_thread = threading.Thread(target=start_api, daemon=True)
            api_thread.start()
        except Exception as e:
            print(f"Error booting API: {e}")

def process_command(line: str) -> Optional[str]:
    """Process special commands and return response."""
    # Commands should start with /
    if not line.startswith('/'):
        return None
        
    command = line[1:].strip().lower()
    
    # Handle place lookup command
    if command.startswith('place '):
        query = command[6:].strip()
        return fetch_place_details(query)
    
    return None

def main(skip_loader: bool = False, skip_api: bool = False) -> None:
    """
    Main function that runs the interactive chat loop.

    Initializes the chatbot environment and starts an interactive CLI session.
    Handles user input and displays model responses in a loop until the user exits
    by entering an empty line.

    Special commands:
    /place <query> - Look up place details using Google Places API

    :param skip_loader: If True, skips the document loader prompt. Useful for testing.
    :type skip_loader: bool
    :param skip_api: If True, skips the API server prompt. Useful for testing.
    :type skip_api: bool
    :return: None
    :raises: KeyboardInterrupt if user interrupts with Ctrl+C
    :raises: Exception for any other runtime errors
    """
    if not skip_loader:
        load()

    if not skip_api:
        api()

    # Configuration constants
    thread_config = {"configurable": {"thread_id": "abc123"}}

    print("  /place <query> - Look up place details")
    while True:
        try:
            line = input("\nllm>> ").strip()
            if line:
                # Check for special commands
                command_result = process_command(line)
                if command_result is not None:
                    print(f"\n{command_result}")
                    continue
                
                result = chatbot_app.invoke(
                    {"input": line},
                    config=thread_config,
                )
                print(f"\n{result['answer']}")
            else:
                break
        except Exception as e:
            print(f"Error with llm input: {e}")


if __name__ == "__main__":
    try:
        main(skip_loader=False, skip_api=False)
    except KeyboardInterrupt:
        print("\nExiting...")
    except Exception as e:
        print(f"Error: {e}")
