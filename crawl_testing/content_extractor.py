import asyncio
import os
import json
import hashlib
from playwright.async_api import async_playwright, Playwright

# --- Configuration ---
LINKS_FILE = "found_links.txt"
OUTPUT_DIR = "crawled_data"
MAX_CONCURRENCY = 10 
semaphore = asyncio.Semaphore(MAX_CONCURRENCY)

def load_links_from_file(filename=LINKS_FILE):
    """Reads URLs from the specified file, stripping duplicates and empty lines."""
    if not os.path.exists(filename):
        print(f"Error: Link file '{filename}' not found. Please run your crawler first.")
        return []
        
    with open(filename, 'r', encoding='utf-8') as f:
        # Use a set to handle duplicates
        urls = set(line.strip() for line in f if line.strip())
        
    print(f"Loaded {len(urls)} unique links from {filename}.")
    return list(urls)

def get_safe_filename(url):
    """Generates a safe, unique filename based on the URL hash (as per your original design)."""
    url_hash = hashlib.sha256(url.encode('utf-8')).hexdigest()
    # Use the first 10 characters of the hash as the unique filename
    return os.path.join(OUTPUT_DIR, f"{url_hash[:10]}.json")

async def worker(p: Playwright, url: str):
    """
    The concurrent unit of work: visits URL, extracts content, and saves it as a JSON file.
    """
    # Use the semaphore to limit concurrency
    async with semaphore:
        browser = None
        output_filepath = get_safe_filename(url)

        # Check if the file already exists to avoid re-crawling
        if os.path.exists(output_filepath):
            print(f"  [SKIP] File already exists for {url}. Path: {os.path.basename(output_filepath)}")
            return

        try:
            # Launch browser instance
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()

            print(f"[{MAX_CONCURRENCY - semaphore._value + 1}/{MAX_CONCURRENCY}] Processing: {url}")
            
            # 1. Navigate and Extract Content
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            
            title = await page.title()
            body_content = await page.locator("body").inner_text()
            
            # 2. Prepare data for JSON output
            data = {
                "url": url,
                "page_title": title,
                "full_content": body_content, # Storing full content for later cleaning
                "full_content_length": len(body_content),
                # Storing a snippet for quick debugging/review
                "page_content_snippet": body_content[:500] + "..." if len(body_content) > 500 else body_content,
            }
            
            # 3. Save to JSON file
            with open(output_filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
                
            print(f"  [SAVED] Content extracted and saved: {os.path.basename(output_filepath)}")
            
        except Exception as e:
            # Handle navigation/extraction errors
            print(f"  [ERROR] Failed to process {url}: {e}")
        finally:
            if browser:
                await browser.close()


async def extract_content():
    """Reads links and runs concurrent workers to crawl and save content."""
    
    # --- PHASE 0: SETUP ---
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    urls_to_process = load_links_from_file()
    
    if not urls_to_process:
        print("Exiting extraction: No links to process.")
        return

    print(f"\n--- STARTING CONCURRENT CONTENT EXTRACTION ({len(urls_to_process)} links) ---")
    print(f"Outputting JSON files to directory: {OUTPUT_DIR}")
    
    async with async_playwright() as p:
        
        # Create a list of worker tasks for all URLs
        tasks = [worker(p, url) for url in urls_to_process]
        
        # Run all tasks concurrently
        await asyncio.gather(*tasks)
            
    print(f"\n--- CONTENT EXTRACTION COMPLETE ---")


if __name__ == "__main__":
    try:
        # You need to run the main async function
        asyncio.run(extract_content())
    except KeyboardInterrupt:
        print("\nProcess interrupted by user.")
    except Exception as e:
        print(f"\nAn unhandled error occurred: {e}")
