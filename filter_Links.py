import asyncio
import aiohttp
from bs4 import BeautifulSoup
import json

# -------- CONFIG --------
INPUT_FILE = "found_Links.txt"
OUTPUT_FILE = "results3.json"
MAX_CONCURRENT = 20   # number of requests to run at once (avoid overloading sites)
amountFetched = 0
# -------------------------

async def fetch(session, url):
    """Fetch the HTML of a single URL and log errors."""
    global amountFetched
    if amountFetched % 1000 == 0:
        print(amountFetched)
    amountFetched += 1

    try:
        async with session.get(url, timeout=15) as response:
            if response.status == 200:
                return await response.text()
            else:
                # Log failed URL
                with open("failed_urls.txt", "a", encoding="utf-8") as f:
                    f.write(f"{url}\n")
                return None

    except Exception as e:
        # Log failed URL
        with open("failed_urls.txt", "a", encoding="utf-8") as f:
            f.write(f"{url}\n")
        return None


def parse_html(html, url):
    """Extract visible text content (not metadata) from the webpage."""
    soup = BeautifulSoup(html, "html.parser")

    # Remove scripts, styles, and other non-visible elements
    for tag in soup(["script", "style", "noscript", "header", "footer", "nav", "form", "iframe"]):
        tag.decompose()

    # Get visible text
    text = soup.get_text(separator="\n", strip=True)

    # Optionally, keep only meaningful lines (filtering out junk)
    lines = [line for line in text.splitlines() if len(line.strip()) > 40]  # remove very short lines
    cleaned_text = "\n".join(lines)

    # Optional: still capture title for context
    title = soup.title.string.strip() if soup.title and soup.title.string else None

    return {
        "url": url,
        "title": title,
        "content": cleaned_text
    }


async def process_url(sem, session, url, results):
    """Fetch + parse one URL with concurrency limit."""
    async with sem:
        html = await fetch(session, url)
        if html:
            data = parse_html(html, url)
            results.append(data)


async def main():
    # Load all links
    with open(INPUT_FILE, "r") as f:
        urls = [line.strip() for line in f if line.strip()]

    results = []
    sem = asyncio.Semaphore(MAX_CONCURRENT)

    async with aiohttp.ClientSession() as session:
        tasks = [process_url(sem, session, url, results) for url in urls]
        await asyncio.gather(*tasks)

    # Save to JSON
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"✅ Done! Scraped {len(results)} pages saved to {OUTPUT_FILE}")

# Run
if __name__ == "__main__":
    asyncio.run(main())