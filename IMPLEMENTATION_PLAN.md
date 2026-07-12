# Wellness Document RAG Chatbot Implementation Plan

Provide a brief description of the problem, any background context, and what the change accomplishes.
This plan details the end-to-end development of a privacy-first, grounded RAG chatbot for healthcare and wellness documents. It includes hybrid retrieval (ChromaDB semantic search + BM25), cross-encoder reranking, and grounded generation with Groq, all delivered through a Streamlit UI with robust security guardrails.

## Proposed Changes

---

### Phase 1: Project Setup and Configuration
Create foundational directories and Pydantic configuration.
- `config/settings.py`
- `src/models/schemas.py`
- `.env.example`

---

### Phase 2: Ingestion & Document Processing
Implement file loaders, metadata extraction, conservative text cleaning, structure-aware chunking, and hashing.
- `src/loaders/`
- `src/preprocessing/`
- `src/utils/hashing.py`

---

### Phase 3: Indexing & Hybrid Retrieval
Setup local embeddings, ChromaDB persist logic, BM25 indexing, Rank Fusion, and CrossEncoder reranking.
- `src/indexing/`
- `src/retrieval/`

---

### Phase 4: Generation & Safety
Integrate Groq Python SDK, prompt formulation, prompt-injection guardrails, and post-generation citation validation.
- `src/generation/`
- `src/safety/`

---

### Phase 5: Streamlit Interface
Develop the frontend, state management, and display logic for answers, evidence, and citations.
- `app.py`

---

### Phase 6: Scripts & Sample Data
Write the ingestion script, create fictional sample documents, and implement Pytest testing and the evaluation script.
- `ingest.py`
- `evaluate.py`
- `tests/`
- `data/sample_documents/`

---

### Phase 7: Final Polish
Add requirements, `pyproject.toml`, Dockerfile, `.gitignore`, and the `README.md`.
- `README.md`
- `Dockerfile`

## Verification Plan

### Automated Tests
- Run `python -m pytest` utilizing the provided fictional data. Check coverage of file parsing, RAG pipeline components, hybrid retrieval logic, and citations.

### Manual Verification
- Execute `python ingest.py --sample` to ensure the ingestion pipeline successfully stores chunks locally.
- Execute `streamlit run app.py` (validate it starts).
- Verify Groq LLM generations conform strictly to structured outputs and validation steps.
