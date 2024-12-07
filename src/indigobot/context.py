import readline  # Required for using arrow keys in CLI
from typing import Sequence

from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import START, StateGraph

from typing_extensions import Annotated, TypedDict

from indigobot.config import llms, vectorstores

llm = llms["gpt"]
chatbot_retriever = vectorstores["gpt"].as_retriever()


class ChatState(TypedDict):
    """
    A dictionary that represents the state of a chat interaction/history.
    """

    input: str
    chat_history: Annotated[Sequence[BaseMessage], add_messages]
    context: str
    answer: str


def call_model(state: ChatState):
    """
    Call the model with the given state and return the response.

    :param state: The state containing input, chat history, context, and answer.
    :type state: ChatState
    :return: Updated state with chat history, context, and answer.
    :rtype: dict
    """
    response = chatbot_rag_chain.invoke(state)
    return {
        "chat_history": [
            HumanMessage(state["input"]),
            AIMessage(response["answer"]),
        ],
        "context": response["context"],
        "answer": response["answer"],
    }


### Main program - Contextualize question ###
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

### Main program - Answer question ###
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
