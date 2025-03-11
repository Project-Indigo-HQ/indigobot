"""
This is the main chatbot program/file for conversational capabilities and info distribution.
"""

import chainlit as cl

from indigobot.context import invoke_indybot
from indigobot.utils.etl.custom_loader import start_loader


def main(cl_message: cl.Message) -> None:
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

    start_loader()
    if cl_message:
        # Configuration constants
        thread_config = {"configurable": {"thread_id": cl.context.session.id}}
        response = invoke_indybot(cl_message, thread_config=thread_config)
        if response:
            return response
        else:
            return "No response from chatbot!"

    # Prevents infinite loop when run directly
    return "No input received."


if __name__ == "__main__":
    main()
