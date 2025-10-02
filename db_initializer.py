import asyncio
import os
import sys
import chromadb
from playwright.async_api import async_playwright, Playwright
from semantic_storage import store_content_and_embed, CHROMA_CLIENT, CRAWL_COLLECTION
from urllib.parse import urljoin, urlparse

# --- Globals ---
# Limit the number of concurrent browser page accesses
MAX_CONCURRENCY = 10 
semaphore = asyncio.Semaphore(MAX_CONCURRENCY)
DB_PATH = "./vector_db"
LINKS_FILE = "found_links.txt"

def init_vector_db(db_path=DB_PATH):
    """Initializes the Chroma PersistentClient and sets the global collection."""
    global CHROMA_CLIENT, CRAWL_COLLECTION
    print(f"Initializing Chroma DB at: {db_path}")
    
    # Use PersistentClient to save data to disk
    CHROMA_CLIENT = chromadb.PersistentClient(path=db_path)
    
    # Get or create the collection
    CRAWL_COLLECTION = CHROMA_CLIENT.get_or_create_collection(
        name="web_crawl_data",
    )
    # Assign back to the module to make it globally available for store_content_and_embed
    import semantic_storage
    semantic_storage.CHROMA_CLIENT = CHROMA_CLIENT
    semantic_storage.CRAWL_COLLECTION = CRAWL_COLLECTION
    
    print(f"Collection 'web_crawl_data' ready. Documents currently stored: {CRAWL_COLLECTION.count()}")
    return CRAWL_COLLECTION.count()

def load_links_from_file(filename=LINKS_FILE):
    """Reads URLs from the specified file, stripping duplicates and empty lines."""
    if not os.path.exists(filename):
        print(f"Error: Link file '{filename}' not found. Please crawl first.")
        return []
        
    with open(filename, 'r', encoding='utf-8') as f:
        # Use a set to automatically handle duplicates during loading
        urls = set(line.strip().rstrip('/') for line in f if line.strip())
        
    print(f"Loaded {len(urls)} unique links from {filename}.")
    return list(urls)

async def worker(p: Playwright, url: str):
    """
    The concurrent unit of work: visits URL, extracts content, and embeds it.
    This worker does NOT scrape new links; it only processes existing ones.
    """
    # Use the semaphore to limit concurrency
    async with semaphore:
        browser = None
        try:
            # We skip URLs already processed and stored in Chroma
            if CRAWL_COLLECTION.get(ids=[url], include=[])['ids']:
                print(f"  [SKIP] {url} already in DB.")
                return

            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()

            print(f"[{MAX_CONCURRENCY - semaphore._value + 1}/{MAX_CONCURRENCY}] Processing: {url}")
            
            # 1. Navigate and Extract Content
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            
            title = await page.title()
            body_content = await page.locator("body").inner_text()
            
            # 2. Store Content and Embed (Call to semantic_storage)
            await store_content_and_embed(url, title, body_content)
            
        except Exception as e:
            # Handle navigation/extraction errors (e.g., 404s, timeouts)
            print(f"  [ERROR] Failed to load/embed {url}: {e}")
        finally:
            if browser:
                await browser.close()


async def populate_db():
    """Reads links and runs concurrent workers to populate Chroma."""
    
    # --- PHASE 0: SETUP ---
    initial_count = init_vector_db()
    urls_to_process = load_links_from_file()
    
    if not urls_to_process:
        print("Exiting population: No links to process.")
        return

    print(f"--- STARTING DB POPULATION ({len(urls_to_process)} links) ---")
    print(f"Running with a maximum concurrency of {MAX_CONCURRENCY}.")
    
    async with async_playwright() as p:
        
        # Create a list of worker tasks for all URLs
        tasks = [worker(p, url) for url in urls_to_process]
        
        # Run all tasks concurrently and wait for them all to complete
        # Running a single large batch is efficient for this specific step
        await asyncio.gather(*tasks)
            
    final_count = CRAWL_COLLECTION.count() if CRAWL_COLLECTION else 0
    new_docs = final_count - initial_count
    
    print(f"\n--- DB POPULATION COMPLETE ---")
    print(f"Documents added in this run: {new_docs}")
    print(f"Total documents now stored in Chroma: {final_count}")


if __name__ == "__main__":
    try:
        asyncio.run(populate_db())
    except KeyboardInterrupt:
        print("\nProcess interrupted by user.")
    except Exception as e:
        print(f"\nAn unhandled error occurred: {e}")
