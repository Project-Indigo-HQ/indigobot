"""
This initializes the program's main ReAct conversational agent with tools and
capabilities for caching and information retrieval.
"""

from langchain.tools.retriever import create_retriever_tool
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent

from indigobot.config import llm, vectorstore
from indigobot.utils.caching import cache_response, get_cached_response
from indigobot.utils.places_tool import lookup_place_tool

chatbot_retriever = vectorstore.as_retriever()


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
        print(f"Error invoking indybot: {e}")
        return "It seems an error has occurred."


retriever_tool = create_retriever_tool(
    chatbot_retriever,
    "retrieve_documents",
    "Search and return information about documents as inquired by user.",
)

tools = [retriever_tool, lookup_place_tool]

system_prompt = """
You are a cheerful assistant and your job is to answer questions/provide 
information about social services in Portland, Oregon. Use pieces of 
retrieved context to answer user questions. Use 3 sentences at most and 
keep answers concise. Do not answer questions that don't have to do with your job.
1. Use your `retriever_tool` to search your vectorstore when you need 
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
)
