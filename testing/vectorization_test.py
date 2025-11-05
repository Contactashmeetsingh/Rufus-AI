import os
import time
import json
import requests
from typing import List, Dict, Any
from dotenv import load_dotenv

# Load variables from .env file into the environment
load_dotenv()

# --- Configuration ---
# API_KEY is now loaded securely from the .env file.
# The variable name should match what you put in your .env file (e.g., GEMINI_API_KEY=...)
API_KEY = os.environ.get('GEMINI_API_KEY')
EMBEDDING_MODEL_NAME = "text-embedding-004"
EMBEDDING_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/{}:embedContent"


def embed_content(texts: List[str], api_key: str, model: str) -> List[List[float]]:
    """
    Calls the Gemini Embedding API for texts, implementing exponential backoff.
    """
    if not api_key:
        print("ERROR: API_KEY is missing. Check your .env file for 'GEMINI_API_KEY'.")
        return []

    # Prepare the request components
    headers = {'Content-Type': 'application/json'}
    # Use the API Key in the query parameter for simple REST calls
    url = EMBEDDING_API_URL.format(model) + f"?key={api_key}"

    embeddings = []

    for i, text in enumerate(texts):
        # Payload for individual text
        single_payload = {
            "model": model,
            "content": { "parts": [{"text": text}] }
        }

        # Exponential Backoff Parameters
        max_retries = 5
        base_delay = 1.0

        for attempt in range(max_retries):
            try:
                print(f"[{i+1}/{len(texts)}] Requesting embedding...")
                response = requests.post(url, headers=headers, data=json.dumps(single_payload))
                response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)

                result = response.json()
                embedding = result['embedding']['values']
                embeddings.append(embedding)
                print(f"[{i+1}/{len(texts)}] Success.")
                break # Exit retry loop on success

            except requests.exceptions.RequestException as e:
                # Handle network, rate limit, or authentication issues
                status_code = response.status_code if 'response' in locals() else 'Unknown'
                print(f"[EMBED FAIL] Status {status_code}. Retrying in {base_delay * (2 ** attempt)}s...")

                if attempt < max_retries - 1:
                    time.sleep(base_delay * (2 ** attempt)) # Exponential delay
                else:
                    print(f"[EMBED FAIL] Failed after {max_retries} attempts for text: '{text}'.")
                    return []

            except Exception as e:
                print(f"An unexpected error occurred: {e}")
                return []


    return embeddings

if __name__ == "__main__":
    texts_to_embed = [
        "The RAG pipeline is the future of accurate language models.",
        "Artificial intelligence models are rapidly changing the industry.",
        "Vector databases enable fast and accurate semantic search."
    ]

    if API_KEY:
        print("\n--- STARTING EMBEDDING PROCESS ---")
        embedded_vectors = embed_content(texts_to_embed, API_KEY, EMBEDDING_MODEL_NAME)

        if embedded_vectors:
            print("\n--- EMBEDDING RESULTS ---")
            print(f"Successfully vectorized {len(embedded_vectors)} documents.")
            print(f"Vector dimension: {len(embedded_vectors[0])}\n")

            # Print out the vectors
            for i, vector in enumerate(embedded_vectors):
                print(f"--- Vector {i+1} for Text: '{texts_to_embed[i][:30]}...' ---")
                # Print the first 5 values for inspection
                print(f"Snippet (first 5 values): {vector[:5]}")
                print("-" * 20)

    else:
        print("\n--- SETUP REQUIRED ---")
        print("Please create a file named '.env' in your project directory")
        print("and add your key using the format: GEMINI_API_KEY='YOUR_KEY_HERE'")