import chromadb
from typing import List, Dict, Optional
from embedding_client import get_embedding # Import the async embedding client
import uuid

# --- Globals ---
CHROMA_CLIENT: Optional[chromadb.Client] = None
CRAWL_COLLECTION: Optional[chromadb.Collection] = None

# --- Configuration ---
CHUNK_SIZE = 1000 
CHUNK_OVERLAP = 200 # Overlap to maintain context between chunks

def chunk_text(text: str, chunk_size: int, overlap: int) -> List[str]:
    """
    Splits a large text block into overlapping chunks for better embedding context.
    """
    if not text or len(text) <= chunk_size:
        return [text]

    chunks = []
    start = 0
    
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        
        # Determine the next starting point, accounting for overlap
        start += (chunk_size - overlap)
        if start >= len(text) - overlap:
             # Ensure the last chunk includes the end of the text
             if len(text) - chunk_size > 0 and len(chunks[-1]) != len(text[len(text) - chunk_size:]):
                 chunks.append(text[len(text) - chunk_size:])
             break

    # Clean up empty strings or duplicates resulting from edge cases
    return list(set([c.strip() for c in chunks if c.strip()]))


async def store_content_and_embed(url: str, title: str, content: str):
    """
    Chunks the content, gets embeddings for each chunk asynchronously, and stores 
    the data and vectors in the Chroma collection.
    """
    if CRAWL_COLLECTION is None:
        print("ERROR: Chroma collection not initialized. Cannot store content.")
        return

    chunks = chunk_text(content, CHUNK_SIZE, CHUNK_OVERLAP)
    
    print(f"  [STORE] Chunking complete. Generated {len(chunks)} chunks for {url}")
    
    document_ids = []
    documents = []
    metadatas = []
    vectors = []
    
    for i, chunk in enumerate(chunks):
        # AWAIT the asynchronous embedding call
        vector = await get_embedding(chunk) 

        if vector is None:
            print(f"  [FAIL] Skipping chunk {i+1} due to missing embedding vector.")
            continue
            
        # Create a unique ID for this chunk
        chunk_id = f"{url}_{uuid.uuid4()}"
        
        document_ids.append(chunk_id)
        documents.append(chunk)
        vectors.append(vector)
        
        # Store metadata linking the chunk back to the source document
        metadatas.append({
            "source_url": url,
            "title": title,
            "chunk_index": i
        })

    if document_ids:
        # Batch insert into the Chroma collection
        CRAWL_COLLECTION.add(
            ids=document_ids,
            embeddings=vectors,
            documents=documents,
            metadatas=metadatas
        )
        print(f"  [SUCCESS] Stored {len(document_ids)} chunks for {url} in ChromaDB.")
    else:
        print(f"  [FAIL] No valid chunks were generated or stored for {url}.")
        

async def semantic_search(query: str, top_k: int = 5) -> List[Dict]:
    """
    Performs a semantic search against the vector database using the query's embedding.
    """
    if CRAWL_COLLECTION is None:
        print("ERROR: Chroma collection not initialized. Cannot search.")
        return []

    # Get the embedding vector for the user's query
    query_vector = await get_embedding(query)
    
    if query_vector is None:
        print("ERROR: Could not generate embedding for query.")
        return []
        
    # Query the Chroma collection
    results = CRAWL_COLLECTION.query(
        query_embeddings=[query_vector],
        n_results=top_k,
        include=['metadatas', 'documents', 'distances'] # Also get the distance/score
    )

    # Format the results into a cleaner list of dictionaries
    formatted_results = []
    if results and results['ids'] and results['ids'][0]:
        for i in range(len(results['ids'][0])):
            formatted_results.append({
                "proximity_score": results['distances'][0][i],
                "url": results['metadatas'][0][i]['source_url'],
                "title": results['metadatas'][0][i]['title'],
                "content_chunk": results['documents'][0][i]
            })
            
    return formatted_results