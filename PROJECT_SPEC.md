# Wellness Document RAG Chatbot - Project Specification

## 1. Business Requirement
Build an end-to-end Document Intelligence Chatbot for a healthcare and wellness company. The chatbot allows authorized users to ask questions in natural language and receive answers grounded *strictly* in a provided set of 15 highly confidential healthcare/wellness documents.

## 2. Required Answer Behaviour
* **A. Answered:** Clear, grounded answer with a summary, key details (if applicable), and explicit source citations (document, page/section, exact supporting text, evidence strength).
* **B. Insufficient evidence:** Neutral statement explicitly rejecting the question if it cannot be answered purely using the provided context.
* **C. Conflicting sources:** Neutral explanation of conflicts, presenting both sides with citations, advising the user to verify.
* **D. Safety refusal:** Refusal for diagnosis, emergency guidance, medication recommendations, or inappropriate secret extraction.

## 3. Strict Document-Only Policy
* No external search or knowledge generation.
* No fabrication of sources, page numbers, or text.
* Zero external internet requests for document enrichment.

## 4. Privacy and Confidentiality
* Fictional sample documents are to be used for development.
* Real documents will be placed in `data/documents/` but are strictly excluded from source control (along with vector stores, API keys, etc.).
* Document processing and embedding must occur locally (ChromaDB + Sentence Transformers).
* Only minimal context goes to the Groq API for generation.

## 5. Technology Stack
* Python 3.11
* Streamlit
* Groq Python SDK
* ChromaDB
* Sentence Transformers (bge-small-en-v1.5) & CrossEncoder (ms-marco-MiniLM-L-6-v2)
* PyMuPDF, python-docx, python-pptx, rank-bm25
* Pydantic, pydantic-settings, python-dotenv
* NumPy, pytest, pathlib

## 6. Required Architecture
* **Ingestion:** File Validation -> Metadata Extraction -> Conservative Cleaning -> Structure-Aware Chunking -> Local Embeddings -> Persistent ChromaDB & BM25 Storage.
* **Retrieval:** Semantic Retrieval + BM25 Keyword Retrieval -> Reciprocal Rank Fusion (RRF) -> Deduplication -> CrossEncoder Reranking -> Evidence Assessment.
* **Generation:** Strict Grounded Prompts via Groq -> Structured Output Validation -> Citation Validation -> Safe Streamlit Response.

## 7. Structure & Configuration
* Pydantic-based configuration management from `.env`.
* Mandatory modular architecture (`src/loaders`, `src/preprocessing`, `src/indexing`, `src/retrieval`, `src/generation`, `src/safety`, `src/evaluation`, `src/utils`).

## 8. Security & Resistance
* Mitigate prompt injections.
* Do not parse commands embedded in text as system instructions.
* Do not expose API keys, internal paths, or errors in the UI.
* Provide an explicit Healthcare Disclaimer.
