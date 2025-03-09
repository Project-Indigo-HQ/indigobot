Installation
============

Requirements
------------

Indigobot requires Python 3.9 or later. 
NOTE: This program has only been tested with Python 3.12 (not 3.13)
The following dependencies are required:

* langchain and related packages
* chromadb
* pydantic
* openai
* beautifulsoup4

Basic Installation
------------------

You can install Indigobot directly from the repository:

.. code-block:: bash

   git clone https://github.com/Project-Indigo-HQ/indigobot.git
   cd indigobot
   python -m venv venv
   source venv/bin/activate  # On Windows use: venv\Scripts\activate
   pip install -r requirements.txt
   pip install -e .

Environment Setup
-----------------

Create a `.env` file in the project root with the following variables:

.. code-block:: bash

   OPENAI_API_KEY=your_openai_api_key
   GPLACES_API_KEY=your_google_places_api_key
   CHROMA_PERSIST_DIRECTORY=./chroma_db