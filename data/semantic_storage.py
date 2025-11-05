import asyncio
import chromadb
from embedding_client import get_embedding 

# Global Chroma variables, initialized externally by db_initializer.py
CHROMA_CLIENT = None
CRAWL_COLLECTION = None

async def store_content_and_embed(url, title, content):
    """Generates an embedding and stores the document in the Chroma collection."""
    global CRAWL_COLLECTION
    if not CRAWL_COLLECTION:
        print("Error: Chroma collection not initialized.")
        return False
    
    # Check if the document (URL) already exists using the URL as the unique ID
    # Note: Chroma's get returns results structure even if empty, check 'ids' key.
    if CRAWL_COLLECTION.get(ids=[url], include=[])['ids']:
        # This check is fast for pre-filtering
        print(f"  [STORAGE] Content for {url} already processed (found in Chroma).")
        return True

    # Limit text to 1000 characters for embedding, combining title and content
    text_to_embed = f"{title}. {content[:1000]}"
    vector = await get_embedding(text_to_embed)
    
    if vector:
        try:
            # Chroma add operation
            CRAWL_COLLECTION.add(
                embeddings=[vector],
                documents=[content],
                metadatas=[{"url": url, "title": title}],
                ids=[url] # URL acts as the unique identifier
            )
            print(f"  [STORED] Document embedded and stored in Chroma: {url}")
            return True
        except Exception as e:
            print(f"  [ERROR] Chroma insertion failed for {url}: {e}")
            return False
            
    return False

async def semantic_search(query, top_k=5):
    """
    Performs semantic search by embedding the query and querying the Chroma collection.
    """
    global CRAWL_COLLECTION
    if not CRAWL_COLLECTION or CRAWL_COLLECTION.count() == 0:
        print("Chroma collection is empty or not initialized.")
        return []

    # 1. Get the embedding for the user's query
    query_vector = await get_embedding(query)
    
    if not query_vector:
        print("Could not generate vector for query.")
        return []

    # 2. Query the Chroma collection
    # Chroma handles the vector search (similarity/distance calculation)
    results = CRAWL_COLLECTION.query(
        query_embeddings=[query_vector],
        n_results=top_k,
        include=['metadatas', 'distances'] 
    )

    # 3. Format the results
    formatted_results = []
    
    if results and results['metadatas'] and results['distances']:
        for metadata, distance in zip(results['metadatas'][0], results['distances'][0]):
            # L2 distance: lower distance means higher similarity.
            formatted_results.append({
                "url": metadata.get("url", "N/A"),
                "title": metadata.get("title", "N/A"),
                "proximity_score": distance 
            })
            
    # Sort by the distance (ascending)
    formatted_results.sort(key=lambda x: x["proximity_score"], reverse=False)
    
    return formatted_results
