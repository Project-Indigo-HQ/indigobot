"""
This module provides functionality for managing conversational state, caching responses,
and processing queries through a RAG (Retrieval Augmented Generation) pipeline.
"""

import hashlib
import json
import readline  # Required for using arrow keys in CLI
import sqlite3
from typing import Sequence

from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.schema import AIMessage, BaseMessage, HumanMessage
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import START, StateGraph
from langgraph.graph.message import add_messages
from typing_extensions import Annotated, TypedDict

from indigobot.config import CACHE_DB, llm, vectorstore

chatbot_retriever = vectorstore.as_retriever()


class ChatState(TypedDict):
    """
    This class defines the structure for maintaining chat state throughout
    the conversation, including input, history, context and responses.

    :ivar input: The current user's input text
    :vartype input: str
    :ivar chat_history: Sequence of messages representing the conversation history
    :vartype chat_history: Annotated[Sequence[BaseMessage], add_messages]
    :ivar context: The current conversation context from RAG retrieval
    :vartype context: str
    :ivar answer: The most recent model-generated response
    :vartype answer: str
    """

    input: str
    chat_history: Annotated[Sequence[BaseMessage], add_messages]
    context: str
    answer: str


class ChatbotCache:
    """
    This class provides functionality to store and retrieve chatbot responses
    using SQLite, helping to reduce redundant API calls and improve response times.

    :ivar conn: SQLite database connection
    :vartype conn: sqlite3.Connection
    :ivar cursor: Database cursor for executing SQL commands
    :vartype cursor: sqlite3.Cursor
    """

    def __init__(self, db_path=CACHE_DB):
        """Initialize the cache database connection.

        :param db_path: Path to the SQLite database file
        :type db_path: str
        :raises sqlite3.Error: If database connection fails
        """
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self._create_table()

    def _create_table(self):
        """Create the cache table if it doesn't exist.

        :raises sqlite3.Error: If table creation fails
        """
        self.cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS cache (
            cache_key TEXT PRIMARY KEY,
            input_text TEXT,
            context TEXT,
            response TEXT
        )
        """
        )
        self.conn.commit()

    def _serialize_messages(self, messages):
        """Convert LangChain messages to JSON format.

        :param messages: List of message objects to serialize
        :type messages: List[BaseMessage]
        :return: JSON string representation of messages
        :rtype: str
        """
        return json.dumps(
            [{"type": type(msg).__name__, "content": msg.content} for msg in messages]
        )

    def _deserialize_messages(self, messages_json):
        """Convert stored JSON back to LangChain message objects.

        :param messages_json: JSON string of serialized messages
        :type messages_json: str
        :return: List of reconstructed message objects
        :rtype: List[BaseMessage]
        :raises json.JSONDecodeError: If JSON parsing fails
        """
        messages = json.loads(messages_json)
        deserialized_messages = []
        for msg in messages:
            if msg["type"] == "HumanMessage":
                deserialized_messages.append(HumanMessage(content=msg["content"]))
            elif msg["type"] == "AIMessage":
                deserialized_messages.append(AIMessage(content=msg["content"]))
            else:
                deserialized_messages.append(
                    BaseMessage(content=msg["content"])
                )  # Fallback
        return deserialized_messages

    def get(self, input_text, cache_key, context):
        """Retrieve a cached response.

        :param input_text: Original input text
        :type input_text: str
        :param cache_key: Hash key for cache lookup
        :type cache_key: str
        :param context: Conversation context
        :type context: str
        :return: Deserialized message objects or None if not found
        :rtype: Optional[List[BaseMessage]]
        """
        self.cursor.execute(
            "SELECT response FROM cache WHERE cache_key = ?", (cache_key,)
        )
        result = self.cursor.fetchone()

        if result:
            response_json = result[0]  # Ensure this is a JSON string
            try:
                return self._deserialize_messages(
                    response_json
                )  # Convert back to message objects
            except json.JSONDecodeError:
                return [
                    AIMessage(content=response_json)
                ]  # Fallback to treating as raw text

        return None  # No cached result

    def set(self, input_text, cache_key, context, response):
        """Store a response in the cache.

        :param input_text: Original input text
        :type input_text: str
        :param cache_key: Hash key for storage
        :type cache_key: str
        :param context: Conversation context
        :type context: str
        :param response: Response to cache
        :type response: Union[Dict[str, str], List[BaseMessage]]
        """
        # Ensure response is wrapped in a message object
        if isinstance(response, dict) and "answer" in response:
            response = [AIMessage(content=response["answer"])]

        response_json = self._serialize_messages(response)  # Serialize response
        self.cursor.execute(
            "INSERT OR REPLACE INTO cache (cache_key, input_text, context, response) VALUES (?, ?, ?, ?)",
            (cache_key, input_text, context, response_json),
        )
        self.conn.commit()

    def clear_cache(self):
        """Clear all cached responses.

        :raises sqlite3.Error: If deletion fails
        """
        self.cursor.execute("DELETE FROM cache")
        self.conn.commit()

    def close(self):
        """Close the database connection.

        Should be called when the cache is no longer needed.
        """
        self.conn.close()


# Instantiate the cache - create a sql database version
chatbot_cache = ChatbotCache()


def normalize_text(text):
    """Normalize input text by converting to lowercase and stripping whitespace.

    :param text: Text to normalize
    :type text: Union[str, Any]
    :return: Normalized text string
    :rtype: str
    """
    if isinstance(text, str):
        return text.strip().lower()
    return str(text).strip().lower()


def hash_cache_key(input_text, chat_history, context):
    """Generate a SHA-256 hash key for caching based on conversation state.

    :param input_text: The user's input text
    :type input_text: str
    :param chat_history: Recent conversation history
    :type chat_history: Sequence[BaseMessage]
    :param context: Current conversation context
    :type context: str
    :return: SHA-256 hash of the combined state
    :rtype: str
    """
    # Normalize input_text
    normalized_input = normalize_text(input_text)

    # Normalize chat history (last 2 messages)
    normalized_history = tuple(
        normalize_text(str(message)) for message in chat_history[-2:]
    )

    # Normalize context
    normalized_context = normalize_text(context)

    # Create a key string to hash
    key_string = f"{normalized_input}|{normalized_history}|{normalized_context}"

    # Return a hashed version of the key
    return hashlib.sha256(key_string.encode("utf-8")).hexdigest()


# Cache Decorator with hashed keys
def cache_decorator(func):
    """Decorator that implements caching for model responses.

    :param func: Function to wrap with caching functionality
    :type func: Callable[[ChatState], Dict]
    :return: Wrapped function with caching behavior
    :rtype: Callable[[ChatState], Dict]
    """

    def wrapper(state: ChatState):
        """Wrapper function implementing the caching logic.

        :param state: Current chat state
        :type state: ChatState
        :return: Updated chat state with response
        :rtype: Dict
        """
        input_text = state["input"]

        # Generate a hashed cache key based on input_text and limited chat history
        chat_history = [
            message.content if isinstance(message, BaseMessage) else str(message)
            for message in state["chat_history"]
        ]
        context = str(state["context"])

        # Generate the hash of the cache key
        cache_key = hash_cache_key(input_text, chat_history, context)

        # Check cache first
        cached_response = chatbot_cache.get(input_text, cache_key, context)
        if cached_response:
            # Debug print
            # print(f"Cache hit for input: {input_text}")

            # Ensure cached response is formatted as a dictionary that matches ChatState
            return {
                "chat_history": list(state["chat_history"]) + cached_response,
                "context": context,
                "answer": cached_response[-1].content if cached_response else "",
            }
        else:
            # Debug print
            # print(f"Cache miss for input: {input_text}")
            response = func(state)  # Call the original function
            chatbot_cache.set(
                input_text, cache_key, context, response["chat_history"][-1:]
            )
            return response

    return wrapper


# Updated cached_model_call to use the hashed key for caching
def cached_model_call(input_text: str, chat_history: list, context: str):
    """Make a cached call to the language model.

    :param input_text: User's input text
    :type input_text: str
    :param chat_history: List of previous conversation messages
    :type chat_history: list
    :param context: Current conversation context
    :type context: str
    :return: Model response with updated state
    :rtype: Dict
    """
    # Prepare the state for the model call
    state = {
        "input": input_text,
        "chat_history": chat_history,
        "context": context,
        "answer": "",
    }

    # Call the model and return the response
    return chatbot_rag_chain.invoke(state)


@cache_decorator
def call_model(state: ChatState):
    """Process user input through the model with caching.

    :param state: Current chat state
    :type state: ChatState
    :return: Updated chat state with model response
    :rtype: Dict
    :raises ValueError: If there's an error during model call
    """
    input_text = normalize_text(state["input"])

    # Normalize chat history
    chat_history = [
        (
            HumanMessage(normalize_text(message.content))
            if isinstance(message, BaseMessage)
            else HumanMessage(normalize_text(str(message)))
        )
        for message in state["chat_history"]
    ]

    # Normalize context
    context = normalize_text(state["context"])

    # Call the cached model function
    try:
        response = cached_model_call(input_text, chat_history, context)
    except Exception as e:
        raise ValueError(f"Error in cached_model_call: {e}") from e

    # Update chat history and return the updated state
    updated_chat_history = list(state["chat_history"]) + [
        HumanMessage(input_text),
        AIMessage(response["answer"]),
    ]

    return {
        "chat_history": updated_chat_history,
        "context": response["context"],
        "answer": response["answer"],
    }


# Prompt configuration for question contextualization
contextualize_q_system_prompt = (
    "Reformulate the user's question into a standalone question, "
    "considering the chat history. Return the original question if no reformulation needed."
)
contextualize_q_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", contextualize_q_system_prompt),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
    ]
)
history_aware_retriever = create_history_aware_retriever(
    llm, chatbot_retriever, contextualize_q_prompt
)

# Prompt configuration for answer generation
system_prompt = (
    "You are an assistant that answers questions/provides information about "
    "social services in Portland, Oregon. Use the following pieces of "
    "retrieved context to answer the question. If you don't know the answer, "
    "say that you don't know. Use three sentences maximum and keep the answer concise."
    "\n\n"
    "{context}"
)
qa_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system_prompt),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
    ]
)

question_answer_chain = create_stuff_documents_chain(llm, qa_prompt)
chatbot_rag_chain = create_retrieval_chain(
    history_aware_retriever, question_answer_chain
)

workflow = StateGraph(state_schema=ChatState)
workflow.add_edge(START, "model")
workflow.add_node("model", call_model)

memory = MemorySaver()
chatbot_app = workflow.compile(checkpointer=memory)
