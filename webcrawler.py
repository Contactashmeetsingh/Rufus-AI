import asyncio
from playwright.async_api import async_playwright
from urllib.parse import urljoin, urlparse
import sys

# A set to store visited URLs to prevent infinite recursion
visited_links = set()
# A list to store all discovered unique links
found_links = []

async def crawl_page(page, base_url):
    """
    Crawls a single page, finds all links, and recursively calls itself for
    new, valid links.

    Args:
        page: The Playwright Page object.
        base_url: The base URL of the website to crawl.
    """
    try:
        # Get all 'a' elements on the page
        links = await page.locator("a").all()
        
        for link_element in links:
            # Get the href attribute of the link
            href = await link_element.get_attribute("href")
            
            # Resolve relative URLs to absolute URLs
            if href:
                absolute_url = urljoin(page.url, href)
                
                # Check if the link is within the same domain and hasn't been visited
                if urlparse(absolute_url).netloc == urlparse(base_url).netloc and absolute_url not in visited_links:
                    print(f"Found new link: {absolute_url}")
                    visited_links.add(absolute_url)
                    found_links.append(absolute_url)
                    
                    # Recursively crawl the new link
                    await page.goto(absolute_url, wait_until="domcontentloaded")
                    await crawl_page(page, base_url)
                    await page.go_back() # Go back to the previous page to continue crawling
    except Exception as e:
        print(f"An error occurred while crawling {page.url}: {e}")

async def main(start_url):
    """
    Main function to start the crawling process.
    """
    if not start_url.startswith(("http://", "https://")):
        print("Error: The URL must start with http:// or https://")
        sys.exit(1)

    print(f"Starting crawl from: {start_url}")

    async with async_playwright() as p:
        # Launch a browser in headless mode
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        # Initial navigation
        await page.goto(start_url, wait_until="domcontentloaded")
        
        # Start the recursive crawl
        await crawl_page(page, start_url)
        
        # Close the browser
        await browser.close()

    # Save the found links to a file
    output_filename = "found_links.txt"
    with open(output_filename, "w") as f:
        for link in sorted(found_links):
            f.write(link + "\n")

    print(f"\nCrawling complete. A total of {len(found_links)} unique links were found.")
    print(f"The links have been saved to '{output_filename}'.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python web_crawler.py <URL_to_start_crawling>")
    else:
        start_url = sys.argv[1]
        asyncio.run(main(start_url))
