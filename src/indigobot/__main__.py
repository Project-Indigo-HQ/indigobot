"""
This is the main chatbot program/file for conversational capabilities and info distribution.
"""

import readline  # Required for using arrow keys in CLI
import subprocess
import os
import time

from indigobot.utils.custom_loader import start_loader
from indigobot.context import chatbot_app
from indigobot.config import CURRENT_DIR


def load():
    load_res = input("Would you like to execute the loader? (y/n) ")
    if load_res == "y":
        try:
            start_loader()
        except Exception as e:
            print(f"Error booting loader: {e}")


def api():
    load_res = input("Would you like to enable the API? (y/n) ")
    if load_res == "y":
        try:
            from indigobot.quick_api import start_api
            import threading
            api_thread = threading.Thread(target=start_api, daemon=True)
            api_thread.start()
        except Exception as e:
            print(f"Error booting API: {e}")


def main(skip_loader: bool = False, skip_api: bool = False) -> None:
    """
    Main function that runs the interactive chat loop.
    Handles user input and displays model responses.
    Exits when user enters an empty line.

    Args:
        skip_loader (bool): If True, skips the loader prompt. Useful for testing.
    """
    if not skip_loader:
        load()

    if not skip_api:
        api()

    # Configuration constants
    thread_config = {"configurable": {"thread_id": "abc123"}}

    while True:
        try:
            print()
            line = input("llm>> ")
            if line:
                result = chatbot_app.invoke(
                    {"input": line},
                    config=thread_config,
                )
                print()
                print(result["answer"])
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
