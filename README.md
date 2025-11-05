# 📚 RAG Pipeline: Retrieval-Augmented Generation (RAG) System Status

**Goal:** Shift from simple document storage to a **vector-based RAG system** to fundamentally improve factual accuracy and prevent LLM hallucinations.
**Development Branch:** `feat/data-api-vector-db`

---

## 🚀 System Overview: Retrieval-Augmented Generation (RAG)

The RAG pipeline is a multi-stage system designed to provide the Large Language Model (LLM) with specific, high-quality, and up-to-date context from our source documents **before** it generates a response. This process significantly enhances the model's reliability.



---

## 1. Data Ingestion & Cleaning (Source Data Acquisition)

**Objective:** Successfully acquire raw data from the UC Merced catalog and implement quality control (cleaning) to strip away noisy web boilerplate.

| Component | Task / Design | Current Status | Notes |
| :--- | :--- | :--- | :--- |
| **File Crawler** | Discover and collect all necessary links from the source catalog. | **✅ COMPLETE** | Crawler is operational and saves all discovered URLs to `found_links.txt`. |
| **Raw Scraper** | Retrieve the raw HTML/text content for each URL. | **✅ COMPLETE** | Scraper is wired up and saves raw, uncleaned page content as individual JSON files. |
| **Data Cleaning** | Implement boilerplate, tag, and excessive whitespace removal logic. | **🛠️ TO DO** | **Priority:** Logic is designed but **not yet implemented** in `db_initializer.py`. Data is currently dirty. |

---

## 2. Chunking & Pre-processing (Context Optimization)

**Objective:** Split large, clean documents into smaller, context-friendly chunks to ensure the LLM receives focused, high-quality information during retrieval.

| Component | Task / Design | Current Status | Notes |
| :--- | :--- | :--- | :--- |
| **Chunking Strategy** | Implement Recursive Character Splitting to break cleaned text into optimal context units. | **🛠️ TO DO** | **Blocking:** No chunking logic exists. Each webpage is currently treated as a single, massive chunk. |
| **Chunk Overlap** | Apply a small overlap (e.g., 50-75 tokens) between chunks to maintain contextual flow. | **🛠️ TO DO** | Pending chunking implementation. |

---

## 3. Vectorization (The Semantic Meaning Fix)

**Objective:** Convert cleaned text chunks into actual semantic vectors, replacing placeholder/hash IDs to enable meaningful similarity search.

| Component | Task / Design | Current Status | Notes |
| :--- | :--- | :--- | :--- |
| **Vector DB Setup** | Initialize and connect the persistent ChromaDB client. | **✅ COMPLETE** | ChromaDB client and collection (`web_crawl_data`) are initialized and wired up in relevant scripts. |
| **Embedding Model** | Integrate a reliable model (e.g., **`all-MiniLM-L6-v2`**) to generate true semantic vectors (384-768 dimensions). | **❌ PENDING** | **CRITICAL BLOCKER:** `embedding_client.py` is currently using a generic model/dimensions instead of the required Sentence Transformer logic. **No true semantic vectors are being generated yet.** |

---

## 4. Retrieval Interface (Search & Filtering)

**Objective:** Enable the user to query the system and retrieve the most semantically relevant documents/chunks.

| Component | Task / Design | Current Status | Notes |
| :--- | :--- | :--- | :--- |
| **Search Interface** | Implement an interactive program for users to enter a string query. | **✅ COMPLETE** | `search_interface.py` is fully wired to take a query and return results from the DB. |
| **Relevance Filtering** | Return the Top-K (e.g., K=3) closest items based on vector distance. | **PENDING** | The search function returns 3 results with distance scores. Retrival techniques like cosine have not been tested yet. **However, the scores are meaningless** because the underlying vectors are placeholders (Task 3 is blocking semantic accuracy). |
| **Top-K Optimization** | Optimizing the Top-K value to fit context window | **TODO** | This is close to the final step of RAG implementation. To little of a top-k will result in low information response. Too high top-k can result in cramming information, and increase chances of hallucination. We need to find a balance. |