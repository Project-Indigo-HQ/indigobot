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
    Runs the document loader (scraper) at startup.
    """
    load_res = "y"  # Auto-confirm running the loader
    if load_res == "y":
        try:
            print(" Running document loader...")
            start_loader()
        except Exception as e:
            print(f" Error booting loader: {e}")


def api():
    """
    Starts the API server (FastAPI).
    """
    load_res = "y"  # Auto-confirm starting API
    if load_res == "y":
        try:
            api_thread = threading.Thread(target=start_api, daemon=True)
            api_thread.start()
        except Exception as e:
            print(f" Error booting API: {e}")


def cloud_run_mode():
    """
    Runs the app in Cloud Run mode.
    - Starts the scraper.
    - Starts FastAPI.
    - Keeps the container alive.
    """
    load()
    api()
    print(" IndigoBot is running on Cloud Run...")

    # Prevents container from exiting
    while True:
        time.sleep(3600)  # Sleep for 1 hour


def cli_mode():
    """
    Runs the chatbot in interactive CLI mode.
    """
    load()
    api()

    thread_config = {"configurable": {"thread_id": "abc123"}}
    chat_history = []
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
            print(f" Error with LLM input: {e}")


if __name__ == "__main__":
    try:
        # Uncomment the mode you want to run
        cloud_run_mode()  # Use this for Cloud Run
        # cli_mode()  # Use this for local CLI mode

    except KeyboardInterrupt:
        print("\nExiting...")
    except Exception as e:
        print(f" Error: {e}")
