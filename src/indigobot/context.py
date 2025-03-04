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

import re
import hashlib
import sqlite3
from typing import Dict, List, Optional, Union

from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.schema import AIMessage, BaseMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import START, END, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from typing_extensions import Annotated, TypedDict

from indigobot.config import CACHE_DB, llm, vectorstore
from indigobot.places_tool import places_tool

chatbot_retriever = vectorstore.as_retriever()


def get_cache_connection():
    """Establishes a connection to the SQLite cache database and ensures the table exists."""
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
    """Generate a hash of the query for use as a cache key."""
    return hashlib.sha256(query.encode()).hexdigest()


def cache_response(query: str, response: str):
    """Store a response in the cache."""
    conn = get_cache_connection()
    cursor = conn.cursor()
    query_hash = hash_query(query)
    cursor.execute("INSERT OR REPLACE INTO response_cache (query_hash, response) VALUES (?, ?)", 
                  (query_hash, response))
    conn.commit()
    conn.close()

def get_cached_response(query: str) -> str | None:
    """Retrieve a cached response if available."""
    conn = get_cache_connection()
    cursor = conn.cursor()
    query_hash = hash_query(query)
    cursor.execute("SELECT response FROM response_cache WHERE query_hash = ?", (query_hash,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None

class ChatState(TypedDict):
    """Structure for maintaining chat state throughout the conversation."""
    input: str
    chat_history: Annotated[List[BaseMessage], add_messages]
    context: str
    answer: str


def detect_place_query(state: ChatState) -> Union[str, List[str]]:
    """
    Detect if the user is asking about a place's hours or details.
    Returns the next node to execute: either 'places_lookup' or END.
    """

    if state.get("answer"):
        hours_unknown_patterns = [
            r"I don't have (current|specific) (hours|information) for",
            r"I'm not sure (about|what) the (hours|schedule|location) (are|is) for",
            r"I don't know the (hours|operating hours|schedule|location) (of|for)",
            r"The (hours|schedule|location) (are|is) not (provided|available)",
            r"don't have information about the (hours|location|address)",
        ]
        
        for pattern in hours_unknown_patterns:
            if re.search(pattern, state["answer"], re.IGNORECASE):
                return "places_lookup"
        
        return END
    
    return "model"


def extract_place_name(state: ChatState) -> Optional[str]:
    """Extract potential place name from user query or model response"""
    input_lower = state['input'].lower()
    
    if "trimet" in input_lower:
        if any(term in input_lower for term in ["office", "customer", "service", "center"]):
            return "TriMet Ticket Office Pioneer Square Portland"
    
    if "library" in input_lower:
        if any(term in input_lower for term in ["multnomah", "county", "central", "downtown"]):
            return "Multnomah County Central Library Portland"
    
    if "starbucks" in input_lower and "psu" in input_lower:
        return "Starbucks near Portland State University"
    
    extraction_prompt = f"""
    Extract the name of the place that the user is asking about from this conversation.
    Return just the name of the place without any explanation.
    If no specific place name is mentioned, return 'NONE'.
    
    User question: {state['input']}
    AI response: {state['answer']}
    """
    
    response = llm.invoke(extraction_prompt)
    potential_name = response.content.strip() if hasattr(response, 'content') else response.strip()
    
    if potential_name == "NONE":
        patterns = [
            r"(where is|address of|location of|directions to) (the )?([A-Za-z0-9\s]+)",
            r"(hours|schedule|when is) (the )?([A-Za-z0-9\s]+) (open|closed)",
            r"([A-Za-z0-9\s]+?) (hours|address|phone|contact|website)",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, state['input'], re.IGNORECASE)
            if match:
                groups = match.groups()
                for group in groups:
                    if group and len(group) > 3 and not any(word in group.lower() for word in ["the", "where", "when", "is", "are", "hours", "address"]):
                        potential_name = group.strip()
                        break
    
    if potential_name == "NONE" or len(potential_name) < 3:
        words = state['input'].split()
        nouns = [word for word in words if len(word) > 3 and word.lower() not in ["hours", "where", "when", "open", "closed", "address", "location", "directions"]]
        if nouns:
            potential_name = " ".join(nouns[-2:])
    
    if potential_name and potential_name != "NONE" and not ("portland" in potential_name.lower() or "or" in potential_name.lower()):
        potential_name += " Portland"
    
    return potential_name if potential_name and potential_name != "NONE" else None


def store_place_info_in_vectorstore(place_name: str, place_info: str) -> None:
    """Store the place information in the vectorstore for future retrieval"""
    document_text = f"""
    Information about {place_name}:
    {place_info}
    """
    
    vectorstore.add_texts(
        texts=[document_text],
        metadatas=[{"source": "google_places_api", "place_name": place_name}]
    )


def create_place_info_response(original_answer: str, place_info: str) -> str:
    """Create a new response incorporating the place information"""
    response_prompt = f"""
    The user asked about a place, and our initial response was:
    "{original_answer}"
    
    We've now found this information from Google Places API:
    {place_info}
    
    Create a helpful response that:
    1. Provides the accurate information
    2. Is conversational and friendly
    3. Is concise (maximum 3 sentences for the main information)
    """
    
    new_response = llm.invoke(response_prompt)
    return new_response.content.strip() if hasattr(new_response, 'content') else new_response.strip()


def lookup_place_info(state: ChatState) -> Dict:
    """
    Look up place information using the Google Places API and integrate it into the chat.
    """
    place_name = extract_place_name(state)
    
    if not place_name:
        return {
            "answer": state["answer"] + " I'm unable to find specific information about this place.",
            "chat_history": state["chat_history"] + [
                AIMessage(content=state["answer"] + " I'm unable to find specific information about this place.")
            ],
            "context": state["context"],
        }
    
    print(f"Looking up place: {place_name}")
    place_info = places_tool.lookup_place(place_name)
    
    if "Error" not in place_info and "No results found" not in place_info:
        store_place_info_in_vectorstore(place_name, place_info)
    
    improved_answer = create_place_info_response(state["answer"], place_info)
    
    return {
        "answer": improved_answer,
        "chat_history": state["chat_history"] + [AIMessage(content=improved_answer)],
        "context": state["context"] + f"\n\nPlace information: {place_info}"
    }


def call_model(state: ChatState) -> Dict:
    """Process user input through the RAG model."""
    input_text = state["input"]
    chat_history = state["chat_history"]
    
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
    
    rag_response = chatbot_rag_chain.invoke({
        "input": input_text,
        "chat_history": chat_history,
    })
    

    return {
        "chat_history": list(chat_history) + [
            HumanMessage(content=input_text),
            AIMessage(content=rag_response["answer"]),
        ],
        "context": rag_response.get("context", ""),
        "answer": rag_response["answer"],
        "input": input_text,
    }


def create_chatbot_app():
    workflow = StateGraph(state_schema=ChatState)
    
    workflow.add_edge(START, "model")
    workflow.add_node("model", call_model)
    
    places_node = ToolNode(tools=[lookup_place_info])
    workflow.add_node("places_lookup", places_node)
    
    workflow.add_conditional_edges(
        "model",
        detect_place_query,
        {
            "places_lookup": "places_lookup",
            END: END
        }
    )
    workflow.add_edge("places_lookup", END)
    
    memory = MemorySaver()
    return workflow.compile(checkpointer=memory)


chatbot_app = create_chatbot_app()

def invoke_indybot(input_text, thread_config):
    """Streams the chatbot's response and returns the final content."""
    cached_response = get_cached_response(input_text)
    if cached_response:
        print("Returning cached response")
        return cached_response
        
    try:
        initial_state = {
            "input": input_text,
            "chat_history": [],
            "context": "",
            "answer": ""
        }
        
        result = []
        for chunk in chatbot_app.stream(
            initial_state,
            stream_mode="values",
            config=thread_config,
        ):
            if "messages" in chunk and chunk["messages"]:
                result.append(chunk["messages"][-1])
            elif "answer" in chunk:
                result.append(chunk["answer"])
        
        final_response = None
        if result and hasattr(result[-1], 'content'):
            final_response = result[-1].content
        elif result and isinstance(result[-1], str):
            final_response = result[-1]
        else:
            final_response = "Sorry, I couldn't process that request properly."
            
        cache_response(input_text, final_response)
        
        return final_response
    except Exception as e:
        print(f"Error in invoke_indybot: {str(e)}")
        return f"Error invoking indybot: {str(e)}"
