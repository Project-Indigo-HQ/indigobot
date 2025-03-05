"""
This module provides functionality for managing conversational state, caching responses,
and processing queries through a RAG (Retrieval Augmented Generation) pipeline.

.. moduleauthor:: Team Indigo

Classes
-------
LookupPlacesInput
    Pydantic model for place lookup input validation.

Functions
---------
get_cache_connection
    Establishes a connection to the SQLite cache database and ensures the table exists.
hash_query
    Generate a hash of the query for use as a cache key.
cache_response
    Store a response in the cache.
get_cached_response
    Retrieve a cached response if available.
lookup_place_info
    Retrieves place information using Google Places API.
extract_place_name
    Extracts potential place names from user queries.
store_place_info_in_vectorstore
    Stores place information in the vector database.
create_place_info_response
    Creates responses incorporating place information.
invoke_indybot
    Invokes the chatbot with user input and configuration.
"""

from langchain.tools.retriever import create_retriever_tool
from langchain_core.tools import StructuredTool
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent
from pydantic import BaseModel, Field

from indigobot.config import llm, vectorstore
from indigobot.places_tool import PlacesLookupTool
import sqlite3, hashlib
from indigobot.config import CACHE_DB

chatbot_retriever = vectorstore.as_retriever()

def get_cache_connection():
    """Establish a connection to the SQLite cache database and ensure the cache table exists.

    This function connects to the SQLite database specified by `CACHE_DB` and creates
    a table `response_cache` if it does not already exist. The table stores hashed
    queries as keys and their corresponding responses.

    :return: A connection object to the SQLite database.
    :rtype: sqlite3.Connection
    """
    conn = sqlite3.connect(CACHE_DB)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS response_cache (
            query_hash TEXT PRIMARY KEY,
            response TEXT
        )
    """)
    conn.commit()
    return conn


def hash_query(query: str) -> str:
    """Generate a SHA-256 hash of the query string for use as a cache key.

    This function ensures that identical queries produce the same hash, allowing for
    efficient lookups in the cache.

    :param query: The input query string to be hashed.
    :type query: str
    :return: The SHA-256 hash of the query.
    :rtype: str
    """
    return hashlib.sha256(query.encode()).hexdigest()


def cache_response(query: str, response: str):
    """Store a query-response pair in the cache.

    This function hashes the query and stores it alongside the response in the
    SQLite cache database. If a response for the query already exists, it is replaced.

    :param query: The original user query.
    :type query: str
    :param response: The response to be stored in the cache.
    :type response: str
    """
    conn = get_cache_connection()
    cursor = conn.cursor()
    query_hash = hash_query(query)
    cursor.execute("INSERT OR REPLACE INTO response_cache (query_hash, response) VALUES (?, ?)", 
                   (query_hash, response))
    conn.commit()
    conn.close()


def get_cached_response(query: str) -> str | None:
    """Retrieve a cached response for a given query if available.

    This function checks the SQLite cache database for a previously stored response
    corresponding to the hashed query.

    :param query: The original user query.
    :type query: str
    :return: The cached response if found, otherwise None.
    :rtype: str | None
    """
    conn = get_cache_connection()
    cursor = conn.cursor()
    query_hash = hash_query(query)
    cursor.execute("SELECT response FROM response_cache WHERE query_hash = ?", (query_hash,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None

class LookupPlacesInput(BaseModel):
    """Pydantic model for validating input to the lookup_place_info function.

    :ivar user_input: User's original prompt to be processed by the lookup_place() function
    :vartype user_input: str
    """

    user_input: str = Field(
        ...,
        description="User's original prompt to be processed by the lookup_place() function",
    )


def lookup_place_info(user_input: str) -> str:
    """Look up place information using the Google Places API, load into store, and integrate it into the chat.

    :param user_input: The user's query containing a potential place name
    :type user_input: str
    :return: A response incorporating the place information
    :rtype: str
    :raises Exception: If there's an error extracting the place name
    """
    try:
        place_name = extract_place_name(user_input)
    except Exception as e:
        print(f"Error in extract_place_name: {e}")

    plt = PlacesLookupTool()
    place_info = plt.lookup_place(place_name.content)

    store_place_info_in_vectorstore(place_name.content, place_info)

    improved_answer = create_place_info_response(user_input, place_info)
    return improved_answer


lookup_place_tool = StructuredTool.from_function(
    func=lookup_place_info,
    name="lookup_place_tool",
    description="Use this tool to fill in missing prompt/query knowledge with a Google Places API call.",
    return_direct=True,
    args_schema=LookupPlacesInput,
)


def extract_place_name(place_input):
    """Extract potential place name from user query or model response.

    :param place_input: The text from which to extract a place name
    :type place_input: str
    :return: The language model response containing the extracted place name,
             or None if no place name is found
    :rtype: object
    """

    extraction_prompt = f"""
    Extract the name of the place that the user is asking about from this conversation.
    Return just the name of the place without any explanation.
    If no specific place name is mentioned, return 'NONE'. 
    User question: {place_input}
    """

    potential_name = llm.invoke(extraction_prompt)

    if potential_name == "NONE":
        return None

    return potential_name


def store_place_info_in_vectorstore(place_name: str, place_info: str) -> None:
    """Store the place information in the vectorstore for future retrieval.

    :param place_name: The name of the place
    :type place_name: str
    :param place_info: The information about the place to store
    :type place_info: str
    :return: None
    """
    document_text = f"""Information about {place_name}: {place_info}"""
    vectorstore.add_texts(
        texts=[document_text],
        metadatas=[{"source": "google_places_api", "place_name": place_name}],
    )


def create_place_info_response(original_answer: str, place_info: str) -> str:
    """Create a new response incorporating the place information.

    :param original_answer: The initial response before place information was retrieved
    :type original_answer: str
    :param place_info: The information about the place retrieved from the API
    :type place_info: str
    :return: A new response incorporating the place information
    :rtype: str
    """

    response_prompt = f"""
    The user asked about a place, and our initial response was: "{original_answer}".
    We've now found this information from Google Places API: {place_info}.
    Create a helpful response that provides the accurate information we found
    and is limited to one sentence. If you don't have the info originally 
    asked for, be sure to mention as much.
    """

    new_response = llm.invoke(response_prompt)

    return new_response.content


def invoke_indybot(input, thread_config):
    """Streams the chatbot's response and returns the final content.

    :param input: The user's input message
    :type input: str
    :param thread_config: Configuration for the chat thread
    :type thread_config: dict
    :return: The chatbot's response content or an error message
    :rtype: str
    :raises Exception: Catches and formats any exceptions that occur during invocation
    """
    cached_response = get_cached_response(input)
    if cached_response:
        print("Returning cached response")
        return cached_response

    try:
        result = []
        for chunk in chatbot_app.stream(
            {"messages": [("human", input)]},
            stream_mode="values",
            config=thread_config,
        ):
            result.append(chunk["messages"][-1])

        response = result[-1].content
        cache_response(input, response)
        return response
    except Exception as e:
        return f"Error invoking indybot: {e}"

retriever_tool = create_retriever_tool(
    chatbot_retriever,
    "retrieve_documents",
    "Search and return information about documents as inquired by user.",
)

tools = [retriever_tool, lookup_place_tool]

system_prompt = """
You are a cheerful assistant that answers questions/provides information about 
social services in Portland, Oregon. Use pieces of retrieved context to 
answer user questions. Use 3 sentences at most and keep answers concise.
1. Use your `retriever_tool` to search your vectostore when you need 
additional info for answering. Make sure to take a step where you combine 
all of the info you retrieve and reorganize it to answer the question.
If you cannot find the name of the place in your vectorstore, repsopnd to the 
user with something similar to 'I could not find that place' DO NOT proceed to steps 2 and 3.
2. *IMPORTANT!!: only use `lookup_place_tool` if you have already used `retriever_tool` 
and still don't have specific details about a place such as operating hours, but
you were able to find the name of the place in your vectorstore.*
Do not mention to the user if you are missing info and needed to use 
`lookup_place_tool`, just provide them with the info they asked for.
3. If you still don't know the answer, say something like 'I don't know.'
"""

memory = MemorySaver()
chatbot_app = create_react_agent(
    llm,
    tools=tools,
    prompt=system_prompt,
    checkpointer=memory,
    # store=use for caching(?)
)
