"""
This program uses PyPDFLoader as a file loader and SQL as a vector database.
It loads local PDFs, Python files, and also checks web pages to scrape and consume data.
It currently gets responses from Gpt4o, Gemini, and Claude, though more models could be added.

Usage:

    The interactive prompt accepts natural language queries that will be processed
    by the SQL agent to search and analyze the loaded content.
    
    Example queries:
    - "What tables exist in the database?"
    - "Show me the first 5 documents"
    - "Find documents containing the word 'housing'"
    
    Type 'quit' to exit the interactive prompt.
"""

import os
import readline  # Required for using arrow keys in CLI
import sqlite3

from langchain import hub
from langchain.agents.agent_toolkits import create_retriever_tool
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langchain_community.utilities import SQLDatabase
from langgraph.prebuilt import create_react_agent

from indigobot.config import GPT_DB, llms, vectorstores

llm = llms["gpt"]
vectorstore = vectorstores["gpt"]

# NOTE: not sure best combo/individual options for these
# included_tables = ["documents"]
included_tables = ["documents", "embedding_fulltext_search_content"]


def init_db(db_path=None):
    """
    Initialize the SQLite database with required tables

    :param db_path: Path to the database file. If None, the default GPT_DB path is used.
    :type db_path: str, optional
    :return: An instance of SQLDatabase connected to the specified database path.
    :rtype: SQLDatabase
    :raises Exception: If there is an error initializing the database.
    """
    try:
        # Use provided path or default
        db_file = db_path or GPT_DB

        # Ensure the database directory exists
        os.makedirs(os.path.dirname(db_file), exist_ok=True)

        # First create the database and tables
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()

        # Create the documents table if it doesn't exist
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content TEXT,
                key TEXT,
                string_value TEXT,
                int_value INTEGER,
                float_value REAL,
                bool_value BOOLEAN
            );
            """
        )
        conn.commit()
        conn.close()

        # Then initialize SQLDatabase after tables exist
        db_uri = f"sqlite:///{db_file}"
        db = SQLDatabase.from_uri(
            db_uri, include_tables=included_tables, sample_rows_in_table_info=0
        )

        return db
    except Exception as e:
        print(f"Error initializing database: {e}")
        raise


def main():
    # Initialize database and ensure it's a SQLDatabase instance
    db = init_db(GPT_DB)
    if not isinstance(db, SQLDatabase):
        raise ValueError("Database initialization failed - not a SQLDatabase instance")

    prompt_template = hub.pull("langchain-ai/sql-agent-system-prompt")

    assert len(prompt_template.messages) == 1
    prompt_template.messages[0].pretty_print()
    system_message = prompt_template.format(dialect="SQLite", top_k=5)

    retriever = vectorstore.as_retriever(search_kwargs={"k": 5})
    description = (
        "Use to look up values to filter on. Input is an approximate spelling "
        "of the proper noun, output is valid proper nouns. Use the noun most "
        "similar to the search."
    )

    retriever_tool = create_retriever_tool(
        retriever,
        name="search_proper_nouns",
        description=description,
    )
    toolkit = SQLDatabaseToolkit(db=db, llm=llm)
    tools = toolkit.get_tools()
    tools.append(retriever_tool)

    agent_executor = create_react_agent(llm, tools, state_modifier=system_message)

    while True:
        line = input("llm>> ")
        if line.strip().lower() == "quit":
            print("Exiting the program...")
            break
        if line:
            try:
                for step in agent_executor.stream(
                    {"messages": [{"role": "user", "content": line}]},
                    stream_mode="values",
                ):
                    step["messages"][-1].pretty_print()
            except Exception as e:
                print(f"error: {e}")
        else:
            break


if __name__ == "__main__":
    main()
