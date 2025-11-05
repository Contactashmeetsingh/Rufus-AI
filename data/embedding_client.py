import os
import asyncio
import json
import aiohttp
from typing import List, Optional
from dotenv import load_dotenv

# Load variables from .env file into the environment
load_dotenv()

# --- Configuration ---
# NOTE: The calling script (db_initializer/search_interface) loads the API key from .env.
API_KEY = os.environ.get('GEMINI_API_KEY')
EMBEDDING_MODEL_NAME = "text-embedding-004"
EMBEDDING_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/text-embedding-004:embedContent"

# Global session for connection pooling across multiple asynchronous calls
_session: Optional[aiohttp.ClientSession] = None

def get_session() -> aiohttp.ClientSession:
    """Gets or creates a global aiohttp session for efficient connections."""
    global _session
    if _session is None or _session.closed:
        _session = aiohttp.ClientSession()
    return _session

async def close_session():
    """Closes the global aiohttp session to prevent resource leaks."""
    global _session
    if _session and not _session.closed:
        await _session.close()
        _session = None

async def get_embedding(text: str) -> Optional[List[float]]:
    """
    Generates an embedding vector for the given text using the live Gemini API
    with asynchronous exponential backoff.
    """
    if not API_KEY:
        print("ERROR: API_KEY is missing. Cannot call embedding service.")
        return None
    if not text:
        return None
        
    session = get_session()
    url = f"{EMBEDDING_API_URL}?key={API_KEY}"
    
    payload = {
        "model": EMBEDDING_MODEL_NAME,
        "content": { "parts": [{"text": text}] }
    }
    
    max_retries = 5
    base_delay = 1.0

    print(f"  [EMBED] Requesting vector for text: '{text[:30]}...'")

    for attempt in range(max_retries):
        try:
            async with session.post(url, headers={'Content-Type': 'application/json'}, data=json.dumps(payload)) as response:
                
                if response.status == 200:
                    result = await response.json()
                    # Extract the vector values (768 dimensions)
                    return result['embedding']['values']
                
                elif response.status in [429, 500, 503]:
                    status_code = response.status
                    if attempt < max_retries - 1:
                        delay = base_delay * (2 ** attempt)
                        await asyncio.sleep(delay)
                    else:
                        print(f"[EMBED FAIL] Failed after {max_retries} attempts. Status: {status_code}")
                        return None
                else:
                    print(f"[EMBED FAIL] Non-retryable error (Status: {response.status})")
                    return None

        except aiohttp.ClientConnectorError as e:
            if attempt < max_retries - 1:
                delay = base_delay * (2 ** attempt)
                await asyncio.sleep(delay)
            else:
                print(f"[EMBED FAIL] Failed after {max_retries} attempts due to connection error: {e}")
                return None
        except Exception as e:
            print(f"An unexpected error occurred during embedding: {e}")
            return None
            
    return None