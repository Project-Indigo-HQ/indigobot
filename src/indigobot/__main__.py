"""
This is the main chatbot program/file for conversational capabilities and info distribution.
"""

import readline
import threading

from indigobot.context import invoke_indybot

# from indigobot.quick_api import start_api
from indigobot.utils.custom_loader import start_loader


def main() -> None:
    """
    Main function that runs the interactive chat loop.
    Initializes the chatbot environment and starts an interactive session.
    Handles user input and displays model responses in a loop until the user exits
    by entering an empty line.

    :return: None
    :raises: Exception for any other runtime errors
    """

    try:
        start_loader()
    except Exception as e:
        print(f"Error booting loader: {e}")

        # try:
        #     api_thread = threading.Thread(target=start_api, daemon=True)
        #     api_thread.start()
        # except Exception as e:
        #     print(f"Error booting API: {e}")

    """vv local cli testing vv"""

    thread_config = {"configurable": {"thread_id": "abc123"}}

    while True:
        try:
            line = input("\nllm>> ")
            if line:
                result = invoke_indybot(line, thread_config)
                print(result)

            else:
                print("Exiting chat...")
                break
        except Exception as e:
            print(f"Error with llm input: {e}")

    """^^ local cli testing ^^"""


if __name__ == "__main__":
    main()
