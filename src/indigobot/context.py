"""
This module provides functionality for managing conversational state, caching responses,
and processing queries through a RAG (Retrieval Augmented Generation) pipeline.
"""

import re
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

from indigobot.config import llm, vectorstore
from indigobot.places_tool import places_tool

# Create a retriever for the RAG system
chatbot_retriever = vectorstore.as_retriever()

# Define the state structure for the conversation
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
    # If we already have an answer from the model
    if state.get("answer"):
        # Patterns that indicate missing place information
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
    
    # If we don't have an answer yet, always go to the model first
    return "model"


def extract_place_name(state: ChatState) -> Optional[str]:
    """Extract potential place name from user query or model response"""
    # Direct pattern matching for common places
    input_lower = state['input'].lower()
    
    # Thinking to delete manually checking later
    if "trimet" in input_lower:
        if any(term in input_lower for term in ["office", "customer", "service", "center"]):
            return "TriMet Ticket Office Pioneer Square Portland"
    
    if "library" in input_lower:
        if any(term in input_lower for term in ["multnomah", "county", "central", "downtown"]):
            return "Multnomah County Central Library Portland"
    
    if "starbucks" in input_lower and "psu" in input_lower:
        return "Starbucks near Portland State University"
    
    # Use LLM-based extraction
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
        # Fallback: use regex patterns
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
    
    # If still no name found, extract key nouns as a last resort
    if potential_name == "NONE" or len(potential_name) < 3:
        words = state['input'].split()
        nouns = [word for word in words if len(word) > 3 and word.lower() not in ["hours", "where", "when", "open", "closed", "address", "location", "directions"]]
        if nouns:
            potential_name = " ".join(nouns[-2:])  # Use last two substantial words
    
    # Add location context for better results
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
    # Extract potential place name from the user query or model answer
    place_name = extract_place_name(state)
    
    if not place_name:
        # If we can't extract a place name, return a modified version of the original answer
        return {
            "answer": state["answer"] + " I'm unable to find specific information about this place.",
            "chat_history": state["chat_history"] + [
                AIMessage(content=state["answer"] + " I'm unable to find specific information about this place.")
            ],
            "context": state["context"],
        }
    
    # Look up the place using the Places tool
    print(f"Looking up place: {place_name}")
    place_info = places_tool.lookup_place(place_name)
    
    # If we got place information, store it in the vectorstore for future use
    if "Error" not in place_info and "No results found" not in place_info:
        store_place_info_in_vectorstore(place_name, place_info)
    
    # Create a new response that incorporates the place information
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
    
    # Create a contextualized question
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
    
    # Configure the answer generation prompt
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
    
    # Create the RAG chain
    question_answer_chain = create_stuff_documents_chain(llm, qa_prompt)
    chatbot_rag_chain = create_retrieval_chain(
        history_aware_retriever, question_answer_chain
    )
    
    # Make the call to the RAG system
    rag_response = chatbot_rag_chain.invoke({
        "input": input_text,
        "chat_history": chat_history,
    })
    
    # Update chat history and return the state
    return {
        "chat_history": list(chat_history) + [
            HumanMessage(content=input_text),
            AIMessage(content=rag_response["answer"]),
        ],
        "context": rag_response.get("context", ""),
        "answer": rag_response["answer"],
        "input": input_text,
    }


# Create the workflow graph and compile it
def create_chatbot_app():
    # Create the workflow graph
    workflow = StateGraph(state_schema=ChatState)
    
    # Add nodes to the graph
    workflow.add_edge(START, "model")
    workflow.add_node("model", call_model)
    
    # Add the places lookup node
    places_node = ToolNode(tools=[lookup_place_info])
    workflow.add_node("places_lookup", places_node)
    
    # Add conditional edges based on place query detection
    workflow.add_conditional_edges(
        "model",
        detect_place_query,
        {
            "places_lookup": "places_lookup",
            END: END
        }
    )
    workflow.add_edge("places_lookup", END)
    
    # Compile the workflow
    memory = MemorySaver()
    return workflow.compile(checkpointer=memory)

# Create the chatbot app once
chatbot_app = create_chatbot_app()

def invoke_indybot(input_text, thread_config):
    """Streams the chatbot's response and returns the final content."""
    try:
        # Initialize state with all required fields
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
        
        # Make sure we get a valid response
        if result and hasattr(result[-1], 'content'):
            return result[-1].content
        elif result and isinstance(result[-1], str):
            return result[-1]
        else:
            return "Sorry, I couldn't process that request properly."
    except Exception as e:
        print(f"Error in invoke_indybot: {str(e)}")
        return f"Error invoking indybot: {str(e)}"