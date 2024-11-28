"""
This is the main chatbot program for conversational capabilities and info distribution.
"""

import readline  # Required for using arrow keys in CLI
from typing import Sequence

from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.tools.retriever import create_retriever_tool
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import START, StateGraph
from langgraph.graph.message import add_messages
from typing_extensions import Annotated, TypedDict

from indigobot.config import llms, vectorstores
from indigobot.utils import custom_loader

llm = llms["gpt"]


class State(TypedDict):
    """
    A dictionary that represents the state of a chat interaction/history.

    :param input: The input string from the user.
    :type input: str
    :param chat_history: A sequence of messages representing the chat history.
                         This includes both human and AI messages.
    :type chat_history: Sequence[BaseMessage]
    :param context: The context string used by the model to generate responses.
    :type context: str
    :param answer: The answer generated by the model for the given input and context.
    :type answer: str
    """

    input: str
    chat_history: Sequence[BaseMessage]
    context: str
    answer: str


def call_model(state: State):
    """
    Call the model with the given state and return the response.

    :param state: The state containing input, chat history, context, and answer.
    :type state: State
    :return: Updated state with chat history, context, and answer.
    :rtype: dict
    """
    response = rag_chain.invoke(state)
    return {
        "chat_history": [
            HumanMessage(state["input"]),
            AIMessage(response["answer"]),
        ],
        "context": response["context"],
        "answer": response["answer"],
    }


# Create vectorstore retriever for accessing & displaying doc info & metadata
retriever = vectorstores["gpt"].as_retriever()

### Contextualize question ###
contextualize_q_system_prompt = (
    "Given a chat history and the latest user question "
    "which might reference context in the chat history, "
    "formulate a standalone question which can be understood "
    "without the chat history. Do NOT answer the question, "
    "just reformulate it if needed and otherwise return it as is."
)
contextualize_q_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", contextualize_q_system_prompt),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
    ]
)
history_aware_retriever = create_history_aware_retriever(
    llm, retriever, contextualize_q_prompt
)

### Answer question ###
system_prompt = (
    "You are an assistant for question-answering tasks. "
    "Use the following pieces of retrieved context to answer "
    "the question. If you don't know the answer, say that you "
    "don't know. Use three sentences maximum and keep the "
    "answer concise."
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
rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)

workflow = StateGraph(state_schema=State)
workflow.add_edge(START, "model")
workflow.add_node("model", call_model)

memory = MemorySaver()
app = workflow.compile(checkpointer=memory)

retriever_tool = create_retriever_tool(retriever, "my_retriever", "my_description")
tools = [retriever_tool]

# Configuration constants
THREAD_CONFIG = {"configurable": {"thread_id": "abc123"}}


def main(skip_loader: bool = False) -> None:
    """
    Main function that runs the interactive chat loop.
    Handles user input and displays model responses.
    Exits when user enters an empty line.

    Args:
        skip_loader (bool): If True, skips the loader prompt. Useful for testing.
    """
    if not skip_loader:
        load_res = input("Would you like to execute the loader? (y/n) ")
        if load_res == "y":
            custom_loader.main()

    print("What kind of questions do you have about the following resources?")
    # Iterate over documents and dump metadata
    document_data_sources = set()
    for doc_metadata in retriever.vectorstore.get()["metadatas"]:
        document_data_sources.add(doc_metadata["source"])
    for doc in document_data_sources:
        print(f"  {doc}")
    while True:
        try:
            print()
            line = input("llm>> ")
            if line:
                result = app.invoke(
                    {"input": line},
                    config=THREAD_CONFIG,
                )
                print()
                print(result["answer"])
            else:
                break
        except Exception as e:
            print(e)


if __name__ == "__main__":
    try:
        main(skip_loader=False)
    except KeyboardInterrupt:
        print("\nExiting...")
    except Exception as e:
        print(f"Error: {e}")