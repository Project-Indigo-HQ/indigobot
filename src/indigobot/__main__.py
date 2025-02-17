"""
This is the main chatbot program/file for conversational capabilities and info distribution.
"""

import readline  # Required for using arrow keys in CLI
import threading

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


def main(skip_loader: bool = False, skip_api: bool = False) -> None:
    """
    Main function that runs the interactive chat loop.
    Initializes the chatbot environment and starts an interactive session.
    Handles user input and displays model responses in a loop until the user exits
    by entering an empty line.

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

    chat_history = []  # Initialize as a list
    context = ""

    while True:
        try:
            line = input("\nllm>> ")
            if line:
                state = {
                    "input": line,
                    "chat_history": chat_history,
                    "context": context,
                    "answer": "",
                }

                result = chatbot_app.invoke(state, config=thread_config)

                # Update chat history and context
                chat_history = result.get("chat_history", chat_history)
                context = result.get("context", context)

                print(f"\n{result['answer']}")
            else:
                print("Exiting chat...")
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
