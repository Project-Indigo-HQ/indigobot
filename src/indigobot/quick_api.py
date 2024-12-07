import os
from fastapi import FastAPI, HTTPException
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from pydantic import BaseModel
from typing_extensions import Annotated
from typing import Sequence
import uvicorn

from indigobot.context import chatbot_retriever, chatbot_rag_chain


# Define API models
class QueryRequest(BaseModel):
    """Request model for query endpoint"""

    input: str

    class Config:
        json_schema_extra = {
            "example": {"input": "What are the key concepts of LLM agents?"}
        }


class QueryResponse(BaseModel):
    """Response model for query endpoint"""

    answer: str

    class Config:
        json_schema_extra = {
            "example": {"answer": "LLM agents are AI systems that can..."}
        }


class State(BaseModel):
    """
    Pydantic model for chat state validation
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
# NOTE: Changed this to take `rag_chain` as function parameter
async def query_model(request: QueryRequest):
    """
    Query the RAG pipeline with a question.

    The system will:
    1. Retrieve relevant context from the document store
    2. Generate an answer based on the context
    3. Return both the answer and the supporting context

    Raises:
        HTTPException(400): If the input is invalid
        HTTPException(500): If there's an internal error
    """
    if not request.input.strip():
        raise HTTPException(status_code=400, detail="Input query cannot be empty")

    try:
        # Initialize state with empty chat history if none provided
        state = State(input=request.input, chat_history=[], context="").model_dump()
        response = chatbot_rag_chain.invoke(state)
        # Format context from documents into a concise string
        context = ""
        if isinstance(response.get("context"), list):
            # Extract just the service descriptions from the documents
            contexts = []
            for doc in response["context"]:
                content = doc.page_content
                # Try to extract service description if it exists
                if "service_description" in content:
                    try:
                        import json

                        data = json.loads("{" + content.split("{", 1)[1])
                        desc = data.get("service_description", "")
                        if desc:
                            if len(desc) > 150:
                                desc = desc[:150] + "..."
                            contexts.append(desc)
                    except Exception as e:
                        # Fallback to simple truncation if JSON parsing fails
                        if len(content) > 150:
                            content = content[:150] + "..."
                        contexts.append(content)
                        print(
                            f"JSON parsing failed; falling back to simple truncation; Exception: {e}"
                        )
                else:
                    # Simple truncation for non-service content
                    if len(content) > 150:
                        content = content[:150] + "..."
                    contexts.append(content)

            context = "\n• ".join(contexts)
        else:
            context = str(response.get("context", "No context available"))
            if len(context) > 450:
                context = context[:450] + "..."

        return QueryResponse(answer=response["answer"])
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")


@app.get("/", summary="Health check", response_description="Basic server status")
async def root():
    """
    Health check endpoint to verify the API is running.
    """
    return {"status": "healthy", "message": "RAG API is running!", "version": "1.0.0"}


@app.get(
    "/sources",
    summary="List available sources",
    response_description="List of document sources in the system",
)
# NOTE: Changed this to take `retriever` as function parameter
async def list_sources():
    """
    List all document sources available in the vector store.
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
    """Start FastAPI"""
    # Get port from environment variable or use default 8000
    port = int(os.getenv("PORT", 8000))
    host = "0.0.0.0"  # Explicitly bind to all interfaces
    print(f"\nStarting server on http://{host}:{port}")
    print("To access from another machine, use your VM's external IP address")
    print(f"Make sure your GCP firewall allows incoming traffic on port {port}\n")

    try:
        uvicorn.run(
            "indigobot.context:chatbot_app",
            host=host,
            port=port,
            reload=True,
            access_log=True,  # Enable access logging
        )
    except Exception as e:
        print(f"Failure running Uvicorn: {e}")


if __name__ == "__main__":
    try:
        start_api()
    except KeyboardInterrupt:
        print("\nExiting...")
    except Exception as e:
        print(f"Error: {e}")
