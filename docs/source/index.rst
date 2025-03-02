IndigoBot Documentation
=======================

Welcome to IndigoBot's documentation. This project provides a sophisticated RAG (Retrieval-Augmented Generation) system using LangChain for intelligent document processing and retrieval.

Features
--------

* **Advanced RAG Implementation**: Uses state-of-the-art OpenAI LLM models
* **Intelligent Web Crawling**: Built-in crawler with rate limiting and retry mechanisms
* **Vectorstore Management**: Uses Chroma for efficient document embedding storage
* **Places Information Tool**: Integration with Google Places API for location-based information
* **Modular Architecture**: Easily extensible for custom document processors

Quick Start
-----------

To get started with IndigoBot:

.. code-block:: bash

   git clone https://github.com/yourusername/indigobot
   cd indigobot
   python -m venv venv
   source venv/bin/activate  # On Windows use: venv\Scripts\activate
   pip install -r requirements.txt
   pip install -e .

Configuration
-------------

The project requires several environment variables to be set:

* ``OPENAI_API_KEY``: Your OpenAI API key
* ``GPLACES_API_KEY``: Your Google Places API key for the Places Lookup Tool

Core Components
---------------

* **Document Loader**: Processes various document formats
* **Web Crawler**: Intelligently crawls and extracts web content
* **Vector Store**: Manages document embeddings
* **RAG Engine**: Coordinates retrieval and generation
* **Places Lookup Tool**: Retrieves and formats place information

Module Documentation
--------------------

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   modules
   indigobot
   indigobot.config
   indigobot.context
   indigobot.places_tool
   indigobot.quick_api
   indigobot.utils

License
-------

This project is licensed under the GNU General Public License v3.0 - see the LICENSE file for details.

Indices and Tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
