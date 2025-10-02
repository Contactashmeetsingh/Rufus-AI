import asyncio
import sys
import os
from playwright.async_api import async_playwright
from urllib.parse import urljoin, urlparse

# Import the content extraction utility
from content_extractor import extract_and_save_content, OUTPUT_DIR

# --- Globals for Crawling State ---
# A set to store visited URLs to prevent infinite recursion and duplicate processing
visited_links = set()
# A list to store all discovered unique links to be processed in Phase 2
found_links = []

async def crawl_page(page, base_url):
    """
    Recursively crawls a single page. Its sole responsibility is finding 
    and collecting new, valid, unvisited links.
    """
    current_url = page.url
    print(f"-> Scanning: {current_url}")

    # 1. Find Links and Perform Recursive Crawl
    try:
        # Get all 'a' elements on the page
        links = await page.locator("a").all()
        
        for link_element in links:
            href = await link_element.get_attribute("href")
            
            if href:
                absolute_url = urljoin(current_url, href)
                
                # Normalize and clean the URL (remove fragment identifiers)
                absolute_url = urlparse(absolute_url)._replace(fragment="").geturl()
                
                # Check if the link is within the same domain and hasn't been visited
                if urlparse(absolute_url).netloc == urlparse(base_url).netloc and absolute_url not in visited_links:
                    
                    # Add to visited set immediately to prevent concurrent or future processing
                    visited_links.add(absolute_url)
                    found_links.append(absolute_url)

                    print(f"  [NEW LINK] Found: {absolute_url}")
                    
                    # Recursively crawl the new link
                    # Navigate to the new page
                    await page.goto(absolute_url, wait_until="domcontentloaded")
                    await crawl_page(page, base_url)
                    
                    # Navigate back to the parent page to continue the loop
                    await page.go_back() 

    except Exception as e:
        print(f"  [ERROR] An error occurred while scanning links on {current_url}: {e}")


async def main(start_url):
    """
    Main function to orchestrate the two phases: Crawling and Extraction.
    """
    if not start_url.startswith(("http://", "https://")):
        print("Error: The URL must start with http:// or https://")
        sys.exit(1)

    # Normalize the starting URL
    initial_url = urlparse(start_url)._replace(fragment="").geturl()
    
    # --- PHASE 1: RECURSIVE LINK DISCOVERY ---
    print(f"\n--- PHASE 1: STARTING RECURSIVE LINK DISCOVERY from {initial_url} ---")
    
    async with async_playwright() as p:
        # Launch browser once for traversal efficiency
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        # Add initial URL
        visited_links.add(initial_url)
        found_links.append(initial_url)
        
        # Initial navigation and kick-off the recursion
        await page.goto(initial_url, wait_until="domcontentloaded")
        await crawl_page(page, initial_url)
        
        await browser.close()
        
    print(f"\n--- PHASE 1 COMPLETE: {len(found_links)} unique links discovered ---")
    
    # --- PHASE 2: CONTENT EXTRACTION ---
    print(f"\n--- PHASE 2: STARTING CONTENT EXTRACTION (Saving to {OUTPUT_DIR}) ---")
    
    # Process the discovered links sequentially using the external extractor function
    for i, link in enumerate(found_links):
        print(f"({i+1}/{len(found_links)}) Extracting content for: {link}")
        # Call the external utility function
        await extract_and_save_content(link)
        
    print(f"\n--- PHASE 2 COMPLETE ---")

    # --- FINAL WRITEOUTS ---
    output_link_filename = "found_links.txt"
    with open(output_link_filename, "w", encoding='utf-8') as f:
        # Sort links for consistent output
        for link in sorted(found_links):
            f.write(link + "\n")

    print(f"\nFinal results:")
    print(f"Total unique pages processed: {len(found_links)}")
    print(f"All discovered links saved to: '{output_link_filename}'.")
    print(f"Page contents saved as JSON files in the '{OUTPUT_DIR}' directory.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python recursive_crawler.py <URL_to_start_crawling>")
        print("\nExample: python recursive_crawler.py https://catalog.ucmerced.edu/")
    else:
        start_url = sys.argv[1]
        try:
            asyncio.run(main(start_url))
        except KeyboardInterrupt:
            print("\nCrawl interrupted by user.")
        except Exception as e:
            print(f"\nAn unhandled error occurred in main execution: {e}")
