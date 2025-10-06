import asyncio
import sys
from playwright.async_api import async_playwright, Playwright
from urllib.parse import urljoin, urlparse

# --- Globals for Concurrency and State ---
# Limit the number of concurrent browser page accesses to avoid overwhelming the network/server
MAX_CONCURRENCY = 25
semaphore = asyncio.Semaphore(MAX_CONCURRENCY)

# Sets for managing state quickly (O(1) lookups)
visited_links = set()
# List to store all final, unique links found
found_links = []
# Set of URLs waiting to be processed (the "queue")
urls_to_crawl = set()

def is_same_domain(url1, url2):
    """Checks if two URLs belong to the same domain."""
    netloc1 = urlparse(url1).netloc
    netloc2 = urlparse(url2).netloc
    return netloc1 == netloc2

async def scrape_links(page, base_domain):
    """
    Rapidly extracts all unique, in-domain links from the current page.
    """
    current_url = page.url
    
    # Get all 'a' elements on the page
    links = await page.locator("a").all()
    
    newly_found_count = 0
    
    for link_element in links:
        try:
            href = await link_element.get_attribute("href")
            
            if href:
                absolute_url = urljoin(current_url, href)
                
                # Normalize the URL (remove fragment and ensure no trailing slashes confuse the crawler)
                parsed_url = urlparse(absolute_url)
                normalized_url = parsed_url._replace(fragment="").geturl().rstrip('/')
                
                # Check for same domain and if it has already been processed or queued
                if is_same_domain(normalized_url, base_domain) and normalized_url not in visited_links:
                    
                    # If this is a new, valid link, add it to the queue (urls_to_crawl set)
                    if normalized_url not in urls_to_crawl:
                        urls_to_crawl.add(normalized_url)
                        newly_found_count += 1

        except Exception as e:
            # Silently ignore errors during link attribute parsing
            pass
            
    print(f"  [DISCOVER] {current_url} -> Found {newly_found_count} new links. Queue size: {len(urls_to_crawl)}")


async def worker(p: Playwright, url: str, base_domain: str):
    """
    The concurrent unit of work. Manages a browser page lifecycle for a single URL.
    """
    # Use the semaphore to limit concurrency
    async with semaphore:
        # Launch a new context/page for this specific task
        browser = None
        try:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()

            print(f"[{MAX_CONCURRENCY - semaphore._value + 1}/{MAX_CONCURRENCY}] Visiting: {url}")
            
            # Navigate to the URL
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            
            # Scrape and queue new links
            await scrape_links(page, base_domain)
            
        except Exception as e:
            print(f"  [ERROR] Failed to load/scrape {url}: {e}")
        finally:
            if browser:
                await browser.close()
            
            # Once processed (successfully or not), mark the URL as visited
            visited_links.add(url)
            found_links.append(url)
            

async def main(start_url):
    """
    Orchestrates the concurrent, breadth-first crawling process.
    """
    if not start_url.startswith(("http://", "https://")):
        print("Error: The URL must start with http:// or https://")
        sys.exit(1)

    # Normalize the starting URL and determine the base domain
    initial_url = urlparse(start_url)._replace(fragment="").geturl().rstrip('/')
    base_domain = initial_url
    
    # Add the initial URL to the queue
    urls_to_crawl.add(initial_url)
    
    print(f"Starting concurrent link crawl from: {initial_url}")
    print(f"Running with a maximum concurrency of {MAX_CONCURRENCY}.")
    
    async with async_playwright() as p:
        
        while urls_to_crawl:
            # Get the batch of URLs to process concurrently
            current_batch = list(urls_to_crawl)
            urls_to_crawl.clear() # Clear the queue for the next batch
            
            # Create a list of worker tasks for all URLs in the current batch
            tasks = [worker(p, url, base_domain) for url in current_batch]
            
            # Run all tasks concurrently and wait for them all to complete
            await asyncio.gather(*tasks)
            
            print(f"\n--- Batch Complete. Total links found: {len(found_links)}. Next batch size: {len(urls_to_crawl)} ---\n")
            
            # Stop if the queue is empty (no new links found in the last batch)
            if not urls_to_crawl:
                break
                
    # --- FINAL WRITEOUTS ---
    output_link_filename = "found_links.txt"
    # Sort and save all unique found links
    with open(output_link_filename, "w", encoding='utf-8') as f:
        for link in sorted(found_links):
            f.write(link + "\n")

    print(f"\nCrawling complete. A total of {len(found_links)} unique pages were processed.")
    print(f"All discovered links have been saved to '{output_link_filename}'.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python fast_crawler.py <URL_to_start_crawling>")
        print("\nExample: python fast_crawler.py https://example.com")
    else:
        start_url = sys.argv[1]
        try:
            asyncio.run(main(start_url))
        except KeyboardInterrupt:
            print("\nCrawl interrupted by user.")
        except Exception as e:
            print(f"\nAn unhandled error occurred: {e}")
