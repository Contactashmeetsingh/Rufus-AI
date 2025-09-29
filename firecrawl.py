"""
A polite, domain-limited async web crawler using aiohttp and asyncio.
This is a lightweight reimplementation inspired by open-source "fire" crawlers.

Features:
- Respects robots.txt (basic check)
- Domain-limited (only follows links within the start URL's domain)
- Concurrent requests with a semaphore to limit concurrency
- Simple HTML link extraction using lxml (no heavyweight browser automation)
- Rate limiting (delay between requests)
- Writes discovered URLs to `found_links.txt`

Notes:
- This crawler is intended for educational/testing use only. Always follow the target site's
  terms of service and robots.txt, and avoid high request rates.

Usage:
  python firecrawl.py https://example.com

"""
from __future__ import annotations
import asyncio
import sys
from urllib.parse import urljoin, urlparse
import aiohttp
import time
import re
from typing import Set, List

try:
    from lxml import html
except Exception:
    html = None

# Globals kept simple for this small script
visited: Set[str] = set()
found: Set[str] = set()

USER_AGENT = "firecrawl/0.1 (+https://example.com)"
CONCURRENCY = 5
REQUEST_DELAY = 0.3  # seconds between requests
TIMEOUT = 15

async def fetch(session: aiohttp.ClientSession, url: str) -> str | None:
    """Fetch a URL and return text or None on failure."""
    try:
        async with session.get(url, timeout=TIMEOUT) as resp:
            if resp.status != 200:
                print(f"Skipping {url} (status {resp.status})")
                return None
            ct = resp.headers.get("content-type", "")
            if "text/html" not in ct:
                print(f"Skipping {url} (non-HTML: {ct})")
                return None
            text = await resp.text()
            return text
    except asyncio.TimeoutError:
        print(f"Timeout fetching {url}")
    except Exception as e:
        print(f"Error fetching {url}: {e}")
    return None

LINK_RE = re.compile(r"href=[\"']([^\"'#]+)[\"']", re.I)

def extract_links(base: str, html_text: str) -> List[str]:
    """Extract links from HTML using lxml when available, otherwise fallback to regex."""
    links: List[str] = []
    if html and isinstance(html_text, str):
        try:
            doc = html.fromstring(html_text)
            doc.make_links_absolute(base)
            for el in doc.xpath('//a[@href]'):
                href = el.get('href')
                if href:
                    links.append(href.split('#')[0])
            return links
        except Exception:
            pass

    for m in LINK_RE.finditer(html_text or ""):
        href = m.group(1)
        links.append(urljoin(base, href).split('#')[0])
    return links

async def crawl(start_url: str, max_pages: int = 200):
    parsed = urlparse(start_url)
    base_domain = parsed.netloc

    sem = asyncio.Semaphore(CONCURRENCY)

    connector = aiohttp.TCPConnector(limit_per_host=CONCURRENCY)
    headers = {"User-Agent": USER_AGENT}
    async with aiohttp.ClientSession(connector=connector, headers=headers) as session:
        queue = asyncio.Queue()
        await queue.put(start_url)
        visited.add(start_url)
        found.add(start_url)

        async def worker():
            while not queue.empty() and len(found) < max_pages:
                url = await queue.get()
                async with sem:
                    print(f"Fetching: {url}")
                    text = await fetch(session, url)
                    await asyncio.sleep(REQUEST_DELAY)
                if not text:
                    queue.task_done()
                    continue
                for link in extract_links(url, text):
                    parsed_link = urlparse(link)
                    if parsed_link.netloc != base_domain:
                        continue
                    if link not in visited:
                        print(f" Found link:  {link}")
                        visited.add(link)
                        found.add(link)
                        await queue.put(link)
                queue.task_done()

        workers = [asyncio.create_task(worker()) for _ in range(CONCURRENCY)]
        await queue.join()
        for w in workers:
            w.cancel()

    # write results
    out = "found_links.txt"
    with open(out, 'w') as f:
        for u in sorted(found):
            f.write(u + '\n')
    print(f"Done. Found {len(found)} URLs. Saved to {out}")


def basic_robots_allowed(start_url: str) -> bool:
    """Very small robots.txt check for the start domain's /robots.txt file.
    Returns True if allowed or cannot determine.
    """
    parsed = urlparse(start_url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    try:
        import requests
        r = requests.get(robots_url, timeout=5, headers={"User-Agent": USER_AGENT})
        if r.status_code != 200:
            return True
        text = r.text
        # naive: look for Disallow: /
        for line in text.splitlines():
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if line.lower().startswith('disallow:') and '/' in line:
                parts = line.split(':', 1)
                if len(parts) > 1 and parts[1].strip() == '/':
                    return False
        return True
    except Exception:
        return True


async def main():
    if len(sys.argv) < 2:
        print('Usage: python firecrawl.py <start_url> [max_pages]')
        sys.exit(1)
    start = sys.argv[1]
    max_pages = int(sys.argv[2]) if len(sys.argv) > 2 else 200
    if not start.startswith(('http://', 'https://')):
        print('URL must start with http:// or https://')
        sys.exit(1)

    allowed = basic_robots_allowed(start)
    if not allowed:
        print('robots.txt disallows crawling the root path; aborting')
        sys.exit(1)

    await crawl(start, max_pages)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('\nInterrupted')
