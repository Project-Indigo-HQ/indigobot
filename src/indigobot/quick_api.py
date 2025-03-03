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

import requests
import uvicorn
from fastapi import FastAPI, Header, HTTPException, Request, WebSocket
from fastapi.responses import JSONResponse
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field, ValidationError
from typing_extensions import Annotated

from indigobot.context import chatbot_app, invoke_indybot

CHATWOOT_ACCESS_TOKEN = os.getenv("CHATWOOT_ACCESS_TOKEN")
CHATWOOT_API_URL = os.getenv("CHATWOOT_API_URL", "https://your-chatwoot-instance.com")
CHATWOOT_ACCOUNT_ID = os.getenv("CHATWOOT_ACCOUNT_ID")


def send_message_to_chatwoot(conversation_id, message):
    url = f"{CHATWOOT_API_URL}/api/v1/accounts/{CHATWOOT_ACCOUNT_ID}/conversations/{conversation_id}/messages"
    headers = {
        "api_access_token": CHATWOOT_ACCESS_TOKEN,
        "Content-Type": "application/json",
    }
    payload = {"content": message, "message_type": "outgoing"}

    response = requests.post(url, json=payload, headers=headers)

    if response.status_code == 200:
        print("Message sent back to Chatwoot successfully.")
    else:
        print(f"Failed to send message: {response.status_code} {response.text}")


# Define API models
class QueryRequest(BaseModel):
    """Request model for the query endpoint.

    :param input: The question or query text to be processed by the RAG system.
                 Should be a clear, well-formed question in natural language.
    :type input: str
    """

    input: str

    class Config:
        json_schema_extra = {
            "example": {"input": "What are the key concepts of LLM agents?"}
        }

    @classmethod
    def validate_request(cls, data: dict) -> "QueryRequest":
        """Custom validation to handle various input formats"""
        if isinstance(data, dict):
            if "input" in data:
                return cls(input=str(data["input"]))
            # Try to convert the first value found to input
            for val in data.values():
                return cls(input=str(val))
        # If we get a string directly, use it as input
        if isinstance(data, str):
            return cls(input=data)
        raise ValueError("Invalid input format")


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


class State(BaseModel):
    """Pydantic model for maintaining and validating chat state.

    :param input: The current user input/query.
    :type input: str
    :param chat_history: List of previous chat messages, annotated with add_messages
                        for proper message handling.
    :type chat_history: Sequence[BaseMessage]
    :param context: Retrieved context from the RAG system.
    :type context: str
    :param answer: Generated answer for the current query.
    :type answer: str
    """

    input: str
    chat_history: Annotated[Sequence[BaseMessage], add_messages] = []
    context: str = ""
    answer: str = ""


# FastAPI app initialization
app = FastAPI(
    title="RAG API",
    description="REST API for RAG-powered question answering",
    version="1.0.0",
)


# Define API endpoints
@app.post(
    "/query",
    response_model=QueryResponse,
    summary="Query the RAG system",
    response_description="The answer and supporting context",
)

@app.post("/webhook", response_model=QueryResponse, summary="Webhook endpoint")
async def webhook(request: WebhookRequest, authorization: str = Header(None)):
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

        # Extract message content
        content = request.messages[0].content if request.messages else ""

        # Extract conversation ID directly from the root payload
        conversation_id = request.id  # This should capture 'id=33'

        print(f"Conversation ID: {conversation_id}")

        if not content or not content.strip():
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

@app.middleware("http")
async def log_requests(request: Request, call_next):
    print(f"🔍 Incoming Request: {request.method} {request.url}")
    print(f"📡 User-Agent: {request.headers.get('user-agent')}")
    response = await call_next(request)
    return response


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


@app.get(
    "/sources",
    summary="List available sources",
    response_description="List of document sources in the system",
)
async def list_sources():
    """List all document sources available in the vector store.

    Retrieves unique source identifiers from document metadata in the vector store.

    :return: Dictionary containing list of sources
    :rtype: dict
    :returns: Dictionary with the following keys:
        - sources (list): List of unique source identifiers
    :raises HTTPException: 500 if there's an error accessing the vector store
    """
    try:
        document_data_sources = set()
        for doc_metadata in chatbot_retriever.vectorstore.get()["metadatas"]:
            document_data_sources.add(doc_metadata["source"])
        return {"sources": list(document_data_sources)}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error retrieving sources: {str(e)}"
        )


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
