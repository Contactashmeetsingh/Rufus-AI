import asyncio
import sys
import chromadb
from semantic_storage import semantic_search, CHROMA_CLIENT, CRAWL_COLLECTION
from db_initializer import init_vector_db # Use the initializer function

async def main():
    """Initializes the DB and runs the interactive search loop."""
    
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
            
            search_results = await semantic_search(query, top_k=3)
            
            if search_results:
                print(f"Found {len(search_results)} top results:")
                # Score is Chroma's distance, where LOWER is better
                for i, result in enumerate(search_results):
                    print(f"  {i+1}. Score (Distance): {result['proximity_score']:.4f} | Title: {result['title']}")
                    print(f"     URL: {result['url']}")
            else:
                print("No results found.")

        except EOFError:
            print("\nExiting search loop.")
            break
        except Exception as e:
            print(f"An error occurred during search: {e}")
            break


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nSearch interrupted by user.")
    except Exception as e:
        print(f"\nAn unhandled error occurred: {e}")
