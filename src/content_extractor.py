import os
import json
import hashlib
from playwright.async_api import async_playwright

# The directory where the extracted JSON data will be stored
OUTPUT_DIR = "crawled_data"

def get_safe_filename(url):
    """Generates a safe filename based on the URL hash."""
    url_hash = hashlib.sha256(url.encode('utf-8')).hexdigest()
    # Use the first 10 characters of the hash as the unique filename
    return os.path.join(OUTPUT_DIR, f"{url_hash[:10]}.json")

async def extract_and_save_content(url):
    """
    Launches a dedicated Playwright context, navigates to the URL, 
    extracts the page title and body content, and saves it as a JSON file.
    """
    
    filename = get_safe_filename(url)

    # Skip processing if the file already exists
    if os.path.exists(filename):
        print(f"  [SKIPPED] Content for {url} already saved in {os.path.basename(filename)}")
        return

    # Ensure the output directory exists
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Launch a new, minimal browser context just for this extraction
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()

            # Navigate to the URL and wait for the DOM to load
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            
            # Extract content
            title = await page.title()
            body_content = await page.locator("body").inner_text()
            
            await browser.close()

            # Prepare data for JSON output
            data = {
                "url": url,
                "page_title": title,
                # Store a snippet of the content for quick review
                "page_content_snippet": body_content[:500] + "..." if len(body_content) > 500 else body_content,
                "full_content_length": len(body_content),
            }

            # Write the data to the JSON file
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
                
            print(f"  [SAVED] -> {os.path.basename(filename)}")

    except Exception as e:
        print(f"  [ERROR] Could not process {url} for extraction: {e}")
