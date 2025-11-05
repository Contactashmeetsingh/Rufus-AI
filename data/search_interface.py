import asyncio
import sys
import chromadb
from semantic_storage import semantic_search, CHROMA_CLIENT, CRAWL_COLLECTION
from db_initializer import init_vector_db # Use the initializer function
from embedding_client import close_session # Import the async session closer
from dotenv import load_dotenv # Used to load GEMINI_API_KEY

async def main():
    """Initializes the DB and runs the interactive search loop."""
    
    load_dotenv() # Load environment variables (like GEMINI_API_KEY)
    
    # --- PHASE 0: INITIALIZE VECTOR DB ---
    doc_count = init_vector_db()

    print(f"\n--- PHASE 1: INTERACTIVE SEMANTIC SEARCH ---")
    print(f"Database initialized with {doc_count} documents. Type 'quit' to exit.")

    while True:
        try:
            query = input("\nEnter semantic query: ")
            if query.lower() == 'quit':
                break
            
            if not query.strip():
                continue
                
            print(f"\nSearching for documents semantically similar to: '{query}'...")
            
            # semantic_search is an async function and must be awaited
            search_results = await semantic_search(query, top_k=3)
            
            if search_results:
                print(f"Found {len(search_results)} top results:")
                # Score is Chroma's distance, where LOWER is better (closer to 0)
                for i, result in enumerate(search_results):
                    print(f"  {i+1}. Score (Distance): {result['proximity_score']:.4f} | Title: {result['title']}")
                    print(f"     URL: {result['url']}")
                    print(f"     Snippet: {result['content_chunk'][:150]}...")
            else:
                print("No results found.")

        except EOFError:
            print("\nExiting search loop.")
            break
        except Exception as e:
            print(f"An error occurred during search: {e}")
            break
            
    # Clean up the aiohttp session before exiting
    await close_session()


if __name__ == "__main__":
    try:
        # Run the main async function
        # This wrapper is necessary because the main function uses 'await'
        asyncio.run(main()) 
    except KeyboardInterrupt:
        print("\nSearch interrupted by user.")
    except Exception as e:
        print(f"\nAn unhandled error occurred: {e}")