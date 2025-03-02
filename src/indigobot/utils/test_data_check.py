import numpy as np
from langchain_chroma import Chroma

from indigobot.config import RAG_DIR, vectorstore


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
    return retriever.get_relevant_documents(text)


def check_duplicate(vectorstore, new_item_vector, similarity_threshold=0.9):
    """
    Checks if a new item is a duplicate of any item in the vectorstore.

    :param vectorstore: Vectorstore to check for duplicates
    :type vectorstore: Vectorstore
    :param new_item_vector: Vector of the new item to check for duplicates
    :type new_item_vector: np.array
    :param similarity_threshold: Threshold for similarity between vectors
    :type similarity_threshold: float
    :return: True if the new item is a duplicate, False otherwise
    :rtype: bool
    """
    # FIXME: Chroma is not iterable
    for item in vectorstore:
        similarity = np.dot(item["vector"], new_item_vector)
        if similarity > similarity_threshold:
            return True
    return False


if __name__ == "__main__":
    chroma = Chroma()

    # Test data for checking duplicates-----------------------
    # Retrieve an existing item from the vectorstore
    retriever = vectorstore.as_retriever(
        search_type="mmr", search_kwargs={"k": 1, "fetch_k": 5}
    )
    existing_item = retriever.get_relevant_documents("news")[0]
    existing_item_vector = existing_item["vector"]
    existing_item_metadata = existing_item["metadata"]

    # Add the existing item to the vector store for testing
    vectorstore.add_item(existing_item_vector, existing_item_metadata)

    # New item that is exactly the same as the existing item
    new_item_vector = existing_item_vector  # Same vector as existing item

    # Check for duplicates
    is_duplicate = check_duplicate(vectorstore, new_item_vector)
    print("Is duplicate:", is_duplicate)
    # ---------------------------------------------------------

    results = quary_chroma("Housing")
    print(results)
