 import os                                                                                                                                                                                                                                                                                                                      
 import pytest                                                                                                                                                                                                                                                                                                                  
 import sqlite3                                                                                                                                                                                                                                                                                                                 
 import tempfile                                                                                                                                                                                                                                                                                                                
 from unittest.mock import Mock, patch                                                                                                                                                                                                                                                                                          
                                                                                                                                                                                                                                                                                                                                
 from langchain_community.document_loaders import Document                                                                                                                                                                                                                                                                      
 from langchain_community.utilities import SQLDatabase                                                                                                                                                                                                                                                                          
                                                                                                                                                                                                                                                                                                                                
 from indigobot.utils.sql_agent import (                                                                                                                                                                                                                                                                                        
     init_db,                                                                                                                                                                                                                                                                                                                   
     load_docs,                                                                                                                                                                                                                                                                                                                 
     load_urls,                                                                                                                                                                                                                                                                                                                 
     query_database,                                                                                                                                                                                                                                                                                                            
     format_docs,                                                                                                                                                                                                                                                                                                               
 )                                                                                                                                                                                                                                                                                                                              
                                                                                                                                                                                                                                                                                                                                
 @pytest.fixture                                                                                                                                                                                                                                                                                                                
 def temp_db_path():                                                                                                                                                                                                                                                                                                            
     """Fixture to create a temporary database file"""                                                                                                                                                                                                                                                                          
     with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:                                                                                                                                                                                                                                                         
         db_path = f.name                                                                                                                                                                                                                                                                                                       
     yield db_path                                                                                                                                                                                                                                                                                                              
     os.unlink(db_path)  # Clean up after test                                                                                                                                                                                                                                                                                  
                                                                                                                                                                                                                                                                                                                                
 @pytest.fixture                                                                                                                                                                                                                                                                                                                
 def sample_docs():                                                                                                                                                                                                                                                                                                             
     """Fixture to create sample documents"""                                                                                                                                                                                                                                                                                   
     return [                                                                                                                                                                                                                                                                                                                   
         Document(                                                                                                                                                                                                                                                                                                              
             page_content="Test document 1",                                                                                                                                                                                                                                                                                    
             metadata={"source": "test1.txt", "page": 1}                                                                                                                                                                                                                                                                        
         ),                                                                                                                                                                                                                                                                                                                     
         Document(                                                                                                                                                                                                                                                                                                              
             page_content="Test document 2",                                                                                                                                                                                                                                                                                    
             metadata={"source": "test2.txt", "page": 2, "score": 0.95}                                                                                                                                                                                                                                                         
         )                                                                                                                                                                                                                                                                                                                      
     ]                                                                                                                                                                                                                                                                                                                          
                                                                                                                                                                                                                                                                                                                                
 def test_init_db(temp_db_path):                                                                                                                                                                                                                                                                                                
     """Test database initialization"""                                                                                                                                                                                                                                                                                         
     db = init_db(temp_db_path)                                                                                                                                                                                                                                                                                                 
     assert isinstance(db, SQLDatabase)                                                                                                                                                                                                                                                                                         
                                                                                                                                                                                                                                                                                                                                
     # Verify tables were created                                                                                                                                                                                                                                                                                               
     conn = sqlite3.connect(temp_db_path)                                                                                                                                                                                                                                                                                       
     cursor = conn.cursor()                                                                                                                                                                                                                                                                                                     
                                                                                                                                                                                                                                                                                                                                
     # Check if documents table exists                                                                                                                                                                                                                                                                                          
     cursor.execute("""                                                                                                                                                                                                                                                                                                         
         SELECT name FROM sqlite_master                                                                                                                                                                                                                                                                                         
         WHERE type='table' AND name='documents'                                                                                                                                                                                                                                                                                
     """)                                                                                                                                                                                                                                                                                                                       
     assert cursor.fetchone() is not None                                                                                                                                                                                                                                                                                       
                                                                                                                                                                                                                                                                                                                                
     conn.close()                                                                                                                                                                                                                                                                                                               
                                                                                                                                                                                                                                                                                                                                
 def test_load_docs(temp_db_path, sample_docs):                                                                                                                                                                                                                                                                                 
     """Test loading documents into database"""                                                                                                                                                                                                                                                                                 
     load_docs(sample_docs, temp_db_path)                                                                                                                                                                                                                                                                                       
                                                                                                                                                                                                                                                                                                                                
     # Verify documents were inserted                                                                                                                                                                                                                                                                                           
     results = query_database(                                                                                                                                                                                                                                                                                                  
         "SELECT COUNT(*) FROM documents",                                                                                                                                                                                                                                                                                      
         db_path=temp_db_path                                                                                                                                                                                                                                                                                                   
     )                                                                                                                                                                                                                                                                                                                          
     assert results[0][0] == len(sample_docs)                                                                                                                                                                                                                                                                                   
                                                                                                                                                                                                                                                                                                                                
 @patch('indigobot.utils.sql_agent.AsyncHtmlLoader')                                                                                                                                                                                                                                                                            
 def test_load_urls(mock_loader, temp_db_path):                                                                                                                                                                                                                                                                                 
     """Test loading documents from URLs"""                                                                                                                                                                                                                                                                                     
     mock_docs = [                                                                                                                                                                                                                                                                                                              
         Document(page_content="Web content 1"),                                                                                                                                                                                                                                                                                
         Document(page_content="Web content 2")                                                                                                                                                                                                                                                                                 
     ]                                                                                                                                                                                                                                                                                                                          
     mock_loader_instance = Mock()                                                                                                                                                                                                                                                                                              
     mock_loader_instance.load.return_value = mock_docs                                                                                                                                                                                                                                                                         
     mock_loader.return_value = mock_loader_instance                                                                                                                                                                                                                                                                            
                                                                                                                                                                                                                                                                                                                                
     urls = ["http://example.com"]                                                                                                                                                                                                                                                                                              
     load_urls(urls, temp_db_path)                                                                                                                                                                                                                                                                                              
                                                                                                                                                                                                                                                                                                                                
     mock_loader.assert_called_once_with(urls)                                                                                                                                                                                                                                                                                  
     mock_loader_instance.load.assert_called_once()                                                                                                                                                                                                                                                                             
                                                                                                                                                                                                                                                                                                                                
 def test_format_docs(sample_docs):                                                                                                                                                                                                                                                                                             
     """Test document formatting"""                                                                                                                                                                                                                                                                                             
     formatted = format_docs(sample_docs)                                                                                                                                                                                                                                                                                       
     assert "Test document 1" in formatted                                                                                                                                                                                                                                                                                      
     assert "Test document 2" in formatted                                                                                                                                                                                                                                                                                      
     assert formatted.count("\n\n") == 1  # Documents should be separated by newlines                                                                                                                                                                                                                                           
                                                                                                                                                                                                                                                                                                                                
 def test_query_database(temp_db_path, sample_docs):                                                                                                                                                                                                                                                                            
     """Test database querying"""                                                                                                                                                                                                                                                                                               
     load_docs(sample_docs, temp_db_path)                                                                                                                                                                                                                                                                                       
                                                                                                                                                                                                                                                                                                                                
     # Test basic query                                                                                                                                                                                                                                                                                                         
     results = query_database(                                                                                                                                                                                                                                                                                                  
         "SELECT COUNT(*) FROM documents",                                                                                                                                                                                                                                                                                      
         db_path=temp_db_path                                                                                                                                                                                                                                                                                                   
     )                                                                                                                                                                                                                                                                                                                          
     assert results[0][0] == len(sample_docs)                                                                                                                                                                                                                                                                                   
                                                                                                                                                                                                                                                                                                                                
     # Test query with parameters                                                                                                                                                                                                                                                                                               
     results = query_database(                                                                                                                                                                                                                                                                                                  
         "SELECT * FROM documents WHERE id = ?",                                                                                                                                                                                                                                                                                
         params=(1,),                                                                                                                                                                                                                                                                                                           
         db_path=temp_db_path                                                                                                                                                                                                                                                                                                   
     )                                                                                                                                                                                                                                                                                                                          
     assert len(results) > 0                                                                                                                                                                                                                                                                                                    
                                                                                                                                                                                                                                                                                                                                
 @pytest.mark.parametrize("invalid_query", [                                                                                                                                                                                                                                                                                    
     "SELECT * FROM nonexistent_table",                                                                                                                                                                                                                                                                                         
     "INVALID SQL QUERY",                                                                                                                                                                                                                                                                                                       
 ])                                                                                                                                                                                                                                                                                                                             
 def test_query_database_errors(temp_db_path, invalid_query):                                                                                                                                                                                                                                                                   
     """Test database query error handling"""                                                                                                                                                                                                                                                                                   
     with pytest.raises(sqlite3.Error):                                                                                                                                                                                                                                                                                         
         query_database(invalid_query, db_path=temp_db_path)

