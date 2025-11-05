import asyncio
import os
import sys
from urllib.parse import urlparse, urlunparse
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
    """Converts a URL into a safe, unique filename."""
    try:
        parsed_url = urlparse(url)
        # Combine netloc (domain) and path
        base_name = parsed_url.netloc + parsed_url.path
        
        # Replace non-alphanumeric characters with underscores for safety
        safe_name = ''.join(c if c.isalnum() or c in '._-' else '_' for c in base_name)
        # Ensure it doesn't end with a trailing underscore if path was just '/'
        return f"{safe_name.strip('_')}.txt"
    except Exception:
        # Fallback for very malformed URLs
        return f"malformed_link_{hash(url)}.txt"

async def worker(p: Playwright, url: str):
    """
    The concurrent unit of work: visits URL, extracts content, and saves it to a file.
    """
    # Use the semaphore to limit concurrency
    async with semaphore:
        browser = None
        output_filepath = os.path.join(OUTPUT_DIR, get_safe_filename(url))

        # Check if the file already exists to avoid re-crawling
        if os.path.exists(output_filepath):
            print(f"  [SKIP] File already exists for {url}. Path: {output_filepath}")
            return

        try:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()

            print(f"[{MAX_CONCURRENCY - semaphore._value + 1}/{MAX_CONCURRENCY}] Processing: {url}")
            
            # 1. Navigate and Extract Content
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            
            title = await page.title()
            # Extract content from the body, excluding scripts/styles
            body_content = await page.locator("body").inner_text()
            
            # 2. Prepare content for file storage
            file_content = f"--- URL: {url}\n"
            file_content += f"--- TITLE: {title}\n"
            file_content += f"--- CONTENT START ---\n"
            file_content += body_content
            
            # 3. Save to file
            with open(output_filepath, 'w', encoding='utf-8') as f:
                f.write(file_content)
                
            print(f"  [SAVED] Content extracted and saved: {output_filepath}")
            
        except Exception as e:
            # Handle navigation/extraction errors (e.g., 404s, timeouts)
            print(f"  [ERROR] Failed to load/save {url}: {e}")
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

    print(f"\n--- STARTING CONTENT EXTRACTION ({len(urls_to_process)} links) ---")
    print(f"Outputting files to directory: {OUTPUT_DIR}")
    
    async with async_playwright() as p:
        
        # Create a list of worker tasks for all URLs
        tasks = [worker(p, url) for url in urls_to_process]
        
        # Run all tasks concurrently
        await asyncio.gather(*tasks)
            
    print(f"\n--- CONTENT EXTRACTION COMPLETE ---")


if __name__ == "__main__":
    try:
        asyncio.run(extract_content())
    except KeyboardInterrupt:
        print("\nProcess interrupted by user.")
    except Exception as e:
        print(f"\nAn unhandled error occurred: {e}")
