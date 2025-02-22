from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from indigobot.config import RAG_DIR, vectorstore
import numpy as np

def quary_chroma(text: str):
    """
    Queries the Chroma database for a given text.

    :param text: Text to query in Chroma database
    :type text: str
    :return: Chroma response for the given text
    :rtype: dict
    """
    retriever = vectorstore.as_retriever(
        search_type="mmr", search_kwargs={"k": 1, "fetch_k": 5}
    )
    return retriever.invoke(text)

def create_text_from_item(item):
    """
    Creates a text string from the structured item.

    :param item: Structured item
    :type item: dict
    :return: Concatenated text string
    :rtype: str
    """
    fields = ["general_category", "main_category", "parent_organization", "listing", "service_description", "city", "postal_code", "website", "hours", "phone"]
    text = "".join([str(item[field]) if field in item else "" for field in fields])
    return text

def check_duplicate_v2(vectorstore, new_item, similarity_threshold=0.9):    #FIXME
    """
    Checks if a new item is a duplicate of any item in the vectorstore.

    :param vectorstore: Vectorstore to check for duplicates
    :type vectorstore: Vectorstore
    :param new_item: New item to check for duplicates
    :type new_item: dict
    :param similarity_threshold: Threshold for similarity between vectors
    :type similarity_threshold: float
    :return: True if the new item is a duplicate, False otherwise
    :rtype: bool
    """
    # Initialize the embedding model
    embedding_model = OpenAIEmbeddings()

    # Create a text string from the structured item
    new_item_text = create_text_from_item(new_item)

    # Convert the new item to a vector
    new_item_vector = embedding_model.embed_query(new_item_text)

    # Retrieve existing items from the vectorstore
    retriever = vectorstore.as_retriever(
        search_type="mmr", search_kwargs={"k": 1, "fetch_k": 5}
    )
    existing_items = retriever.invoke(new_item_text)

    # Compare the new item vector with the existing item vectors
    for item in existing_items:
        similarity = np.dot(item["vector"], new_item_vector)
        if similarity > similarity_threshold:
            return True
    return False

def upsert_document():
    pass

if __name__ == "__main__":
    chroma = Chroma()

    # Test data for checking duplicates-----------------------
    # Retrieve an existing item from the vectorstore
    retriever = vectorstore.as_retriever(
        search_type="mmr", search_kwargs={"k": 1, "fetch_k": 5}
    )

    query_text = "123 W Burnside\nPortland OR, 97209"
    results = quary_chroma(query_text)

    is_duplicate = check_duplicate_v2(vectorstore, results[0])
    print(f"Is duplicate: {is_duplicate}")

    """
    for result in results:
        print(result)
        print("\n\n\n")
    """

    print("Test finished.")

