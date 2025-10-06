#!/usr/bin/env python3
"""Rufus-AI pipeline orchestrator

Usage examples:
  python main.py crawl --start-url https://example.com
  python main.py extract
  python main.py populate
  python main.py search
  python main.py all --start-url https://example.com

This script lives at the project root and imports the modules under ./src.
"""
import os
import sys
import argparse
import asyncio

# Ensure ./src is on the import path so we can import project modules.
# Support two locations for this script:
#  - project root (./main.py) where ./src is a sibling directory
#  - inside the src/ directory (./src/main.py) where the project root is the parent
# Determine file directory and compute project root robustly.
file_dir = os.path.dirname(os.path.abspath(__file__))
if os.path.basename(file_dir) == 'src':
    # script lives inside the src/ directory => project root is parent
    ROOT = os.path.dirname(file_dir)
else:
    # script lives at project root => file_dir is root
    ROOT = file_dir

SRC_DIR = os.path.join(ROOT, 'src')
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

# Import project modules (they are async heavy in parts).
# We import the required modules eagerly but treat `webcrawler` as optional.
try:
    import crawler
    import content_extractor
    import db_initializer
    import search_interface
except Exception as e:
    # Import errors for required modules will be surfaced later when commands run.
    _IMPORT_ERROR = e
else:
    _IMPORT_ERROR = None


async def run_crawl(start_url: str, concurrent: bool = True):
    if _IMPORT_ERROR:
        raise RuntimeError(f"Import error when loading modules: {_IMPORT_ERROR}")

    if concurrent:
        print(f"Starting concurrent crawl from {start_url} (crawler.py)")
        await crawler.main(start_url)
    else:
        # webcrawler is optional in this repository layout. Try to import lazily and
        # fall back to the concurrent `crawler` if it's not available.
        try:
            import webcrawler
        except Exception:
            print("[WARN] Serial webcrawler module 'webcrawler' not found; falling back to concurrent crawler")
            await crawler.main(start_url)
        else:
            print(f"Starting serial crawl from {start_url} (webcrawler.py)")
            await webcrawler.main(start_url)


async def run_extract():
    if _IMPORT_ERROR:
        raise RuntimeError(f"Import error when loading modules: {_IMPORT_ERROR}")

    links_file = os.path.join(ROOT, 'src', 'found_links.txt')
    if not os.path.exists(links_file):
        print(f"No links file found at {links_file}. Run crawl first to generate found_links.txt")
        return

    with open(links_file, 'r', encoding='utf-8') as f:
        urls = [line.strip() for line in f if line.strip()]

    if not urls:
        print("No URLs to extract.")
        return

    # Run extractor concurrently with a modest concurrency limit
    semaphore = asyncio.Semaphore(6)

    async def _worker(u):
        async with semaphore:
            try:
                await content_extractor.extract_and_save_content(u)
            except Exception as e:
                print(f"[ERROR] extract failed for {u}: {e}")

    tasks = [_worker(u) for u in urls]
    await asyncio.gather(*tasks)


def run_populate():
    if _IMPORT_ERROR:
        raise RuntimeError(f"Import error when loading modules: {_IMPORT_ERROR}")

    # db_initializer.populate_db is async
    asyncio.run(db_initializer.populate_db())


def run_search():
    if _IMPORT_ERROR:
        raise RuntimeError(f"Import error when loading modules: {_IMPORT_ERROR}")

    # search_interface.main is async interactive REPL
    asyncio.run(search_interface.main())


def main():
    parser = argparse.ArgumentParser(description='Rufus-AI pipeline orchestrator')
    sub = parser.add_subparsers(dest='cmd', required=True)

    p_crawl = sub.add_parser('crawl', help='Run the crawler to produce found_links.txt')
    p_crawl.add_argument('--start-url', required=True, help='Seed URL to start crawling from')
    p_crawl.add_argument('--serial', action='store_true', help='Use the serial webcrawler (no concurrency)')

    p_extract = sub.add_parser('extract', help='Extract pages referenced in found_links.txt and save JSONs')

    p_pop = sub.add_parser('populate', help='Populate the Chroma DB from found links (scrape+embed)')

    p_search = sub.add_parser('search', help='Start the interactive semantic search REPL')

    p_all = sub.add_parser('all', help='Run crawl -> extract -> populate in sequence')
    p_all.add_argument('--start-url', required=True, help='Seed URL to start crawling from')
    p_all.add_argument('--serial', action='store_true', help='Use the serial webcrawler (no concurrency)')

    args = parser.parse_args()

    if args.cmd == 'crawl':
        asyncio.run(run_crawl(args.start_url, concurrent=not args.serial))

    elif args.cmd == 'extract':
        asyncio.run(run_extract())

    elif args.cmd == 'populate':
        run_populate()

    elif args.cmd == 'search':
        run_search()

    elif args.cmd == 'all':
        # 1) crawl
        asyncio.run(run_crawl(args.start_url, concurrent=not args.serial))
        # 2) extract
        asyncio.run(run_extract())
        # 3) populate
        run_populate()


if __name__ == '__main__':
    main()
