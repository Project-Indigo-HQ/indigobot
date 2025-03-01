"""
This module provides functionality for managing conversational state, caching responses,
and processing queries through a RAG (Retrieval Augmented Generation) pipeline.

"""

from langchain.tools.retriever import create_retriever_tool
from langchain_core.tools import StructuredTool
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent
from pydantic import BaseModel, Field

from indigobot.config import llm, vectorstore
from indigobot.places_tool import PlacesLookupTool

chatbot_retriever = vectorstore.as_retriever()


class LookupPlacesInput(BaseModel):
    user_input: str = Field(
        ...,
        description="User's original prompt to be processed by the lookup_place() function",
    )


def lookup_place_info(user_input: str) -> str:
    """
    Look up place information using the Google Places API and integrate it into the chat.

    This function:
    1. Extracts place name from the conversation
    2. Retrieves place details using the Places tool
    3. Updates vectorstore with new information if needed
    4. Prepares an informed response
    """

    print("debug: lookup_place_info called")

    # Extract potential place name from the user query or model answer
    try:
        place_name = extract_place_name(user_input)
    except Exception as e:
        print(f"Error in extract_place_name: {e}")

    # Look up the place using the Places tool
    plt = PlacesLookupTool()
    place_info = plt.lookup_place(place_name.content)

    # If we got place information, store it in the vectorstore for future use
    # NOTE: Want JunFan to look into this function
    # store_place_info_in_vectorstore(place_name.content, place_info)

    # Create a new response that incorporates the place information
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
    """Extract potential place name from user query or model response"""

    # Create a prompt to extract the place name
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
    """Store the place information in the vectorstore for future retrieval"""

    # Format the place info as a document for the vectorstore
    document_text = f"""Information about {place_name}: {place_info}"""
    # Add to vectorstore
    vectorstore.add_texts(
        texts=[document_text],
        metadatas=[{"source": "google_places_api", "place_name": place_name}],
    )


def create_place_info_response(original_answer: str, place_info: str) -> str:
    """Create a new response incorporating the place information"""

    # Create a prompt to generate a new response
    response_prompt = f"""
    The user asked about a place, and our initial response was: "{original_answer}".
    We've now found this information from Google Places API: {place_info}.
    Create a helpful response that provides the accurate information we found
    and is limited to one sentence. If you don't have the info originally 
    asked for, be sure to mention as much.
    """

    new_response = llm.invoke(response_prompt)

    return new_response.content


"""vvv ReAct agent vvv"""


def invoke_indybot(input, thread_config):
    try:
        result = []
        for chunk in chatbot_app.stream(
            {"messages": [("human", input)]},
            stream_mode="values",
            config=thread_config,
        ):
            result.append(chunk["messages"][-1])

        return result[-1].content
    except Exception as e:
        return f"Error invoking indybot: {e}"


retriever_tool = create_retriever_tool(
    chatbot_retriever,
    "retrieve_documents",
    "Search and return information about documents as inquired by user.",
)

tools = [retriever_tool, lookup_place_tool]
# tools = [retriever_tool]

# Prompt configuration for answer generation
system_prompt = """
You are a cheerful assistant that answers questions/provides information about 
social services in Portland, Oregon. Use pieces of retrieved context to 
answer user questions. Use 3 sentences at most and keep answers concise.
1. Use your `retriever_tool` to search your vectostore when you need 
additional info for answering. Make sure to take a step where you combine 
all of the info you retrieve and reorganize it to answer the question.
2. *IMPORTANT!!: only use `lookup_place_tool` if you have already used `retriever_tool` 
and still don't have specific details about a place such as operating hours.* 
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
