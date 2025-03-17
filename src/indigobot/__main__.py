"""
This module serves as the primary entry point for the IndigoBot application.
It initializes the document loader, starts the API server, and maintains
the application's runtime environment.
"""

import threading
import time

from indigobot.quick_api import start_api
from indigobot.utils.etl.custom_loader import start_loader


def main() -> None:
    """
    Main application entry point.
    The API server runs as a daemon thread, allowing the application
    to be terminated gracefully when the main thread exits.

    :return: None
    :raises: Exception: Logs errors from loader or API initialization but continues execution
    """

    try:
        # Initialize document loader to populate vector database
        start_loader()
    except Exception as e:
        print(f"Error booting loader: {e}")

    try:
        # Start API server in a daemon thread
        api_thread = threading.Thread(target=start_api, daemon=True)
        api_thread.start()

        # Keep main thread alive
        while True:
            time.sleep(3600)  # Sleep for one hour
    except Exception as e:
        print(f"Error booting API: {e}")


if __name__ == "__main__":
    main()
