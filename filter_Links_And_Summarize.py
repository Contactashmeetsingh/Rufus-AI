import asyncio
import aiohttp
from bs4 import BeautifulSoup
import json
from transformers import pipeline

# -------- CONFIG --------
INPUT_FILE = "found_links_small.txt"
OUTPUT_FILE = "results6.json"
FAILED_FILE = "failed_urls2.txt"
MAX_CONCURRENT = 20
MAX_TEXT_CHARS = 4000  # limit text size for summarizer
PRINT_EVERY = 100      # show progress every N URLs
amountFetched = 0
# -------------------------

# Initialize summarizer (only once)
summarizer = pipeline("summarization", model="facebook/bart-large-cnn")


async def fetch(session, url):
    """Fetch the HTML of a single URL and log errors."""
    global amountFetched

    try:
        async with session.get(url, timeout=15) as response:
            if response.status == 200:
                html = await response.text()
            else:
                html = None
    except Exception:
        html = None

    # Update progress counter
    amountFetched += 1
    if amountFetched % PRINT_EVERY == 0:
        print(f"✅ Processed {amountFetched} URLs so far...")

    # Log failed URLs
    if html is None:
        with open(FAILED_FILE, "a", encoding="utf-8") as f:
            f.write(f"{url}\n")

    return html


def parse_html(html, url):
    """Extract visible text content (not metadata) from the webpage."""
    soup = BeautifulSoup(html, "html.parser")

    # Remove unwanted elements
    for tag in soup(["script", "style", "noscript", "header", "footer", "nav", "form", "iframe"]):
        tag.decompose()

    # Extract text
    text = soup.get_text(separator="\n", strip=True)
    lines = [line for line in text.splitlines() if len(line.strip()) > 40]
    cleaned_text = "\n".join(lines)

    title = soup.title.string.strip() if soup.title and soup.title.string else None
    return {"url": url, "title": title, "content": cleaned_text}


def summarize_text(text):
    """Summarize extracted text using a pre-trained transformer model."""
    if not text or len(text) < 100:
        return None  # skip very short text

    text = text[:MAX_TEXT_CHARS]  # truncate long text safely
    try:
        # Estimate token length (roughly words/1.3)
        input_length = len(text.split())
        max_len = max(40, min(180, input_length // 2))  # half input size, capped at 180
        min_len = max(20, min(50, input_length // 4))   # quarter input size, capped at 50

        summary = summarizer(
            text,
            max_length=max_len,
            min_length=min_len,
            do_sample=False
        )
        return summary[0]["summary_text"].strip()

    except Exception as e:
        print(f"⚠️ Summarization failed: {e}")
        return None


async def process_url(sem, session, url, results):
    """Fetch + parse + summarize a URL with concurrency control."""
    async with sem:
        html = await fetch(session, url)
        if html:
            data = parse_html(html, url)
            summary = summarize_text(data["content"])
            data["summary"] = summary
            results.append(data)


async def main():
    # Load URLs
    with open(INPUT_FILE, "r") as f:
        urls = [line.strip() for line in f if line.strip()]

    results = []
    sem = asyncio.Semaphore(MAX_CONCURRENT)

    async with aiohttp.ClientSession() as session:
        tasks = [process_url(sem, session, url, results) for url in urls]
        await asyncio.gather(*tasks)

    # Save results
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"🎉 Done! Scraped and summarized {len(results)} pages.")
    print(f"📁 Saved to {OUTPUT_FILE}")


if __name__ == "__main__":
    asyncio.run(main())
