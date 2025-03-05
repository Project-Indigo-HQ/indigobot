"""
FastAPI-based REST API for RAG (Retrieval-Augmented Generation) operations.

This module provides a REST API interface for:
- Querying the RAG system with questions
- Webhook endpoint for external service integration
- Health check endpoint
- Listing available document sources

The API uses FastAPI for HTTP handling and Pydantic for request/response validation.
"""

import json
import os
from typing import Dict, List, Optional, Sequence
import asyncio

import requests
import uvicorn
from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse, PlainTextResponse
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field, ValidationError
from typing_extensions import Annotated

from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from indigobot.context import chatbot_app, invoke_indybot

CHATWOOT_ACCESS_TOKEN = os.getenv("CHATWOOT_ACCESS_TOKEN")
CHATWOOT_API_URL = os.getenv("CHATWOOT_API_URL", "https://your-chatwoot-instance.com")
CHATWOOT_ACCOUNT_ID = os.getenv("CHATWOOT_ACCOUNT_ID")


# Function to extract conversation ID from request
def get_conversation_id(request: Request):
    try:
        body = request.scope.get("body", b"").decode("utf-8")  # Get raw body
        payload = json.loads(body) if body else {}  # Parse JSON if available
        conversation_id = payload.get("id", "unknown")  # Extract conversation ID
        print(f"🔍 Rate Limiting Conversation ID: {conversation_id}")  # Debug log
        return str(conversation_id)
    except Exception as e:
        print(f"❌ Failed to get conversation ID: {e}")
        return "unknown"


limiter = Limiter(key_func=get_conversation_id)


def send_message_to_chatwoot(conversation_id, message):
    url = f"{CHATWOOT_API_URL}/api/v1/accounts/{CHATWOOT_ACCOUNT_ID}/conversations/{conversation_id}/messages"
    headers = {
        "api_access_token": CHATWOOT_ACCESS_TOKEN,
        "Content-Type": "application/json",
    }
    payload = {"content": message, "message_type": "outgoing"}

    try:
        response = requests.post(
            url, json=payload, headers=headers, timeout=5
        )  # ⏳ Add timeout (5 seconds)
        response.raise_for_status()  # Raise an error for bad status codes (4xx, 5xx)

        if response.status_code == 200:
            print("✅ Message sent back to Chatwoot successfully.")
        else:
            print(f"❌ Failed to send message: {response.status_code} {response.text}")

    except requests.Timeout:
        print("⏳❌ Timeout: Chatwoot API took too long to respond!")
    except requests.RequestException as e:
        print(f"❌ Network error sending message: {e}")


class QueryResponse(BaseModel):
    """Response model for the query endpoint.

    :param answer: The generated answer from the RAG system based on the query
                  and retrieved context.
    :type answer: str
    """

    answer: str

    class Config:
        json_schema_extra = {
            "example": {"answer": "LLM agents are AI systems that can..."}
        }


class Message(BaseModel):
    content: Optional[str]  # To capture the user's message


class WebhookRequest(BaseModel):
    """Request model for the webhook endpoint.

    :param message: The message content to be processed.
    :type message: str
    :param source: The source of the webhook request (e.g., 'slack', 'discord').
                  Defaults to 'webhook'.
    :type source: str
    """

    messages: List[Message] = []  # List of messages from Chatwoot
    source: Optional[str] = "webhook"

    class Config:
        extra = "allow"


# FastAPI app initialization
app = FastAPI(
    title="RAG API",
    description="REST API for RAG-powered question answering",
    version="1.0.0",
)

app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)

# Define API endpoints


@app.exception_handler(RateLimitExceeded)
async def ratelimit_handler(request: Request, exc: RateLimitExceeded):
    conversation_id = get_conversation_id(request)

    print(f"⛔ Rate limit exceeded for conversation: {get_conversation_id(request)}")
    return PlainTextResponse(
        "⛔ Rate limit exceeded. Try again later.", status_code=429
    )


@app.post("/webhook", response_model=QueryResponse, summary="Webhook endpoint")
@limiter.limit("10/minute")  # limit to 10 a minute
async def webhook(
    request: Request, webhook_request: WebhookRequest, authorization: str = Header(None)
):
    """Webhook endpoint to receive messages from external services.

    The system performs the following steps:
    1. Process the incoming webhook message
    2. Generate a response using the RAG system
    3. Return the response

    :param request: The webhook request containing the message
    :type request: WebhookRequest
    :return: Response containing the generated answer
    :rtype: QueryResponse
    :raises HTTPException: 400 if the webhook payload is invalid, 500 if there's an internal error
    """
    try:
        print("Webhook triggered!")
        print("Received WebhookRequest:", request)
        payload = await request.json()
        conversation_id = payload.get("id", "unknown")

        messages = payload.get("messages", [])
        content = messages[0].get("content", "")
        conversation_id = messages[0].get("conversation_id", "")

        if not content:
            raise HTTPException(
                status_code=400, detail="Message content cannot be empty"
            )

        # Process with LangChain
        thread_config = {
            "configurable": {
                "session_id": conversation_id,
                "thread_id": conversation_id,
            }
        }
        answer = invoke_indybot(content, thread_config)

        # Send response back to Chatwoot
        if conversation_id:
            send_message_to_chatwoot(conversation_id, answer)
        else:
            print("⚠️ conversation_id is missing!")

        return {"answer": answer}

    except Exception as e:
        print(f"❌ Error: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error processing webhook: {str(e)}"
        )


@app.get("/", summary="Health check", response_description="Basic server status")
async def root():
    """Health check endpoint to verify the API is running.

    :return: Dictionary containing status information
    :rtype: dict
    :returns: Dictionary with the following keys:
        - status (str): Current server status ('healthy')
        - message (str): Status message
        - version (str): API version number
    """
    return {"status": "healthy", "message": "RAG API is running!", "version": "1.0.0"}


def start_api():
    """Start the FastAPI server with Uvicorn.

    Configures the server with the following settings:
        - Listens on all network interfaces (0.0.0.0)
        - Uses port from PORT environment variable (default: 8000)
        - Enables auto-reload for development
        - Enables access logging

    Prints server URL and configuration information to console.

    :raises Exception: If Uvicorn fails to start or encounters runtime errors
    """
    # Get port from environment variable or use default 8000
    """Start FastAPI server"""
    port = int(os.getenv("PORT", 8000))
    host = "0.0.0.0"  # Explicitly bind to all interfaces

    print(f"\nStarting server on http://{host}:{port}")
    print("To access from another machine, use your VM's external IP address")
    print(f"Make sure your GCP firewall allows incoming traffic on port {port}\n")

    try:
        uvicorn.run(app, host=host, port=port, reload=False, access_log=True)
    except Exception as e:
        print(f"Failure running Uvicorn: {e}")


if __name__ == "__main__":
    try:
        start_api()
    except KeyboardInterrupt:
        print("\nExiting...")
    except Exception as e:
        print(f"Error: {e}")
