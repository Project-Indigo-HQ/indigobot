Quick Start
===========

Basic Usage
-----------

After installing Indigobot, you can quickly get started with the following steps:

1. Set up your environment variables (see Configuration section)
2. Run the API server:

.. code-block:: bash

   python -m indigobot

3. The API will be available at http://localhost:8000

Using the API
-------------

You can also interact with Indigobot through its API:

.. code-block:: bash

   # Send a query
   curl -X POST http://localhost:8000/api/query \
     -H "Content-Type: application/json" \
     -d '{"query": "What information do you have about X?", "conversation_id": "123"}'

Example Applications
--------------------

Indigobot can be used for various applications:

- **Document Q&A**: Answer questions based on your document collection
- **Knowledge Base**: Create a searchable knowledge base from your content
- **Customer Support**: Enhance support systems with contextual information
- **Research Assistant**: Help with research by retrieving relevant information
