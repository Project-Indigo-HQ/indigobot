"""
NOTE: For capstone team: this program is mainly a demo of how (sometimes overly) powerful
the Python REPL tool is. It's also a decent example of programmatically creating 
custom agent tools and functions made into agent tools.
Additionally, it shows one way to keep a message history/memory/state.

This program uses a 'ChatOpenAI' 4o based model to examine two methods of creating 
and calling a simple function as a tool that takes a dict type as input. One method 
uses the RunnableLambda library, and the other creates a 'tool_calling_agent' to 
invoke a custom tool function. These functions will concat the keys of a dict with 
a space between each, and total the dict values if they're ints.

The llm could most likely do these operations on its own if you explicitly ask it to, 
so this program is more for exploration/demonstration purposes.
The model is also equipped with the powerful `PythonREPLTool`, which allows it to create and run
Python scripts (e.g. "Create a file named foo").

NOTE: I made it so the model is only supposed to use the REPL tool when asked by user.
This way it actually runs `tca()` function when asked. The `runlam()` function should 
run on its own when user inputs only a dict on the CLI, 
*(must be typed, no c&p)* (e.g.) llm>> {"AA":23,"RR":54,"CC":1}
"""

from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.tools import tool
from langchain_core.runnables import RunnableLambda
from langchain_experimental.tools import PythonREPLTool
from langchain_openai import ChatOpenAI
import subprocess
from typing_extensions import TypedDict


class TcaDict(TypedDict):
    # I think part of the reason for needing this class is to please Pydantic when using `tca()`
    """
    This class allows `tca()` to change keys defined by user-input dict to the TypedDict keys defined below
    """
    key1: int
    key2: int
    key3: int


@tool
def tca(input: TcaDict) -> int:
    """
    Sums values in dictionary and concats keys by leveraging `tool_calling_agent`

    Args:
        input (TcaDict): A dictionary with integer values.

    Returns:
        int: The total of the integer values in the dictionary.
        str: A concatenated string of the keys.
    """
    dict_string = ""
    total = 0
    for string, value in input.items():
        total += value
        dict_string += string + " "
    print("- tca() output:")
    return total, dict_string


@tool
def execute_command(command: str) -> str:
    """
    Executes a command-line command and returns the output.

    Args:
        command (str): The command to execute.

    Returns:
        str: The standard output of the command if successful, otherwise an error message.
    """
    result = subprocess.run(
        command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    )
    if result.returncode == 0:
        return result.stdout
    else:
        return f"Error: {result.stderr}"


def runlam(lambda_input: dict):
    """
    Sums values in dictionary and concats keys by leveraging the `RunnableLambda` library

    Args:
        lambda_input (dict): A dictionary with integer values.

    Prints:
        str: A concatenated string of the keys.
        int: The total of the integer values in the dictionary.
    """
    dict_string = ""
    total = 0
    for string, value in lambda_input.items():
        total += value
        dict_string += string + " "
    print("- runlam() output: ")
    print(f"concat'd string: {dict_string}")
    print(f"total of values: {total}")


model = ChatOpenAI(model="gpt-4o")
memory = InMemoryChatMessageHistory(session_id="test-session")

instructions = """You are an agent that responds to anything the user asks.
You have access to a Python REPL tool, which you can use to execute
python code. Only use your Python REPL tool when asked by user. 
If you get an error when trying to use python, debug your code and try again.
Otherwise, answer user questions as you usually would.
"""

prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "You are a helpful assistant."),
        # First put the history
        ("placeholder", "{chat_history}"),
        # Then the new input
        ("human", "{input}"),
        # Finally the scratchpad
        ("placeholder", "{agent_scratchpad}"),
        instructions,
    ]
)

tools = [execute_command, tca, PythonREPLTool()]
agent = create_tool_calling_agent(model, tools, prompt)
# NOTE: The verbose setting is great for a look into the model's "thoughts" via stdout
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

agent_with_chat_history = RunnableWithMessageHistory(
    agent_executor,
    # This is needed because in most real world scenarios, a session id is needed;
    # It isn't really used here because we are using a simple in memory ChatMessageHistory
    lambda session_id: memory,
    input_messages_key="input",
    history_messages_key="chat_history",
)

config = {"configurable": {"session_id": "test-session"}}

print("Welcome to my HW2 application! These are some of my custom tools:")
for a_tool in tools:
    print(f"  Tool: {a_tool.name} = {a_tool.description}")

while True:
    try:
        line = input("llm>> ")
        if line:
            try:
                runnable = RunnableLambda(runlam(eval(line)))
                as_tool = runnable.as_tool(arg_types=dict)
                as_tool.invoke()

            except Exception:
                result = agent_with_chat_history.invoke({"input": line}, config)[
                    "output"
                ]
                print(result)
        else:
            break
    except Exception as e:
        print(e)
