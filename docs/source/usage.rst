Usage Guide
===========

This guide covers the main use cases and workflows for Indigobot.

Basic Query Example                                                                                                                                                                                                                                                                                                         
-------------------                                                                                                                                                                                                                                                                                                          
                                                                                                                                                                                                                                                                                                                            
.. code-block:: python                                                                                                                                                                                                                                                                                                      
                                                                                                                                                                                                                                                                                                                            
    from indigobot.context import invoke_indybot                                                                                                                                                                                                                                                                             
                                                                                                                                                                                                                                                                                                                                
    # Simple query                                                                                                                                                                                                                                                                                                           
    response = invoke_indybot("What are the key features of our product?", {})                                                                                                                                                                                                                                               
    print(response)      

Document Processing
-------------------

Indigobot currently processes websites and HTML, but can easily 
process document formats like PDF with a few more lines of code.
See LangChain's examples for PDF processing.

Web Crawling
------------

To crawl websites and extract content:

.. code-block:: python

   from indigobot.utils.etl.custom_loader import scrape_main
   
   # Crawl a website with specified depth
   results = scrape_urls(["https://example1.com", "https://example2.com"], depth=2)

Loading Documents
-----------------

To load documents into the system:

.. code-block:: python

   from indigobot.utils.etl.custom_loader import load_docs, load_urls
   
   # Load local documents
   load_docs(["path/to/document1.pdf", "path/to/document2.txt"])
   
   # Load from URLs
   load_urls(["https://example.com/page1", "https://example.com/page2"])

Using the Places Tool
---------------------

The Places Tool can be used to retrieve location information:

.. code-block:: python

   from indigobot.utils.places_tool import lookup_place_info
   
   # Get information about a place
   place_info = lookup_place_info("What are the hours for Central Park?")
   print(place_info)

API Server Example                                                                                                                                                                                                                                                                                                          
------------------                                                                                                                                                                                                                                                                                                            
                                                                                                                                                                                                                                                                                                                            
.. code-block:: python                                                                                                                                                                                                                                                                                                      
                                                                                                                                                                                                                                                                                                                            
    from indigobot.quick_api import start_api                                                                                                                                                                                                                                                                                
    import uvicorn                                                                                                                                                                                                                                                                                                           
                                                                                                                                                                                                                                                                                                                                
    # Configure and start API server                                                                                                                                                                                                                                                                                         
    app = start_api()                                                                                                                                                                                                                                                                                                        
                                                                                                                                                                                                                                                                                                                                
    if __name__ == "__main__":                                                                                                                                                                                                                                                                                               
        uvicorn.run(app, host="0.0.0.0", port=8000)   

API Integration
---------------

To integrate with other systems via the API:

.. code-block:: python

   import requests
   
   # Send a query to the API
   response = requests.post(
       "http://localhost:8000/api/query",
       json={
           "query": "What are the key findings in the latest report?",
           "conversation_id": "user123"
       }
   )
   
   print(response.json())