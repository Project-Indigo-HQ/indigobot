"""
This is the main chatbot program/file for conversational capabilities and info distribution.
Adjusted for cloud run deployment
"""

import readline  # Required for using arrow keys in CLI
import threading
import time

from indigobot.context import chatbot_app
from indigobot.quick_api import start_api
from indigobot.utils.custom_loader import start_loader


def load():
    """
    Prompt user to execute the document loader functionality.

    Asks the user if they want to run the document loader and executes it if confirmed.
    Uses the start_loader() function from custom_loader module.

    :raises: Exception if the loader encounters an error
    """
    load_res = "y"
    #load_res = input("Would you like to execute the loader? (y/n) ")
    if load_res == "y":
        try:
            print(1)
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
    #load_res = input("Would you like to enable the API? (y/n) ")
    load_res = "y"
    if load_res == "y":
        try:
            api_thread = threading.Thread(target=start_api, daemon=True)
            api_thread.start()
        except Exception as e:
            print(f"Error booting API: {e}")
def main():
    """Main function for Cloud Run."""
    load()  # Run the scraper
    api()   # Start FastAPI server

    print("🚀 IndigoBot is running on Cloud Run...")

    # Keep the container alive (Prevents exit)
    while True:
        time.sleep(3600)  # Sleep for 1 hour in a loop


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nExiting...")
    except Exception as e:
        print(f"Error: {e}")
