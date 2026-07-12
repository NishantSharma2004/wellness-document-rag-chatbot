import pickle
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
from rank_bm25 import BM25Okapi
from config.settings import settings
from src.models.schemas import DocumentChunk
from src.utils.exceptions import IndexException

def tokenize(text: str) -> List[str]:
    """Simple lowercase alphanumeric word tokenizer."""
    return re.findall(r'\b\w+\b', text.lower())

class BM25StoreManager:
    def __init__(self):
        self.index_path = Path(settings.BM25_INDEX_PATH)
        self.chunks: List[DocumentChunk] = []
        self.bm25: Optional[BM25Okapi] = None
        self.load_index()

    def load_index(self) -> None:
        """Load index from persistent pickle file if it exists."""
        if self.index_path.exists():
            try:
                with open(self.index_path, "rb") as f:
                    data = pickle.load(f)
                    self.chunks = data.get("chunks", [])
                    # Reconstruct BM25 object
                    corpus = [tokenize(c.text) for c in self.chunks]
                    if corpus:
                        self.bm25 = BM25Okapi(corpus)
            except Exception as e:
                # If loading fails, we just start fresh
                self.chunks = []
                self.bm25 = None

    def save_index(self) -> None:
        """Persist index to a pickle file."""
        if not self.chunks:
            # If empty, remove index file if it exists
            if self.index_path.exists():
                self.index_path.unlink()
            return
        
        try:
            self.index_path.parent.mkdir(parents=True, exist_ok=True)
            # Pickling BM25Okapi directly is supported, but to be safe and avoid serialization issues,
            # we serialize the chunks list and reconstruct on load.
            data = {"chunks": self.chunks}
            with open(self.index_path, "wb") as f:
                pickle.dump(data, f)
        except Exception as e:
            raise IndexException(f"Failed to persist BM25 index: {str(e)}") from e

    def build_index(self, chunks: List[DocumentChunk]) -> None:
        """Rebuild or initialize BM25 from the provided chunks."""
        self.chunks = chunks
        corpus = [tokenize(c.text) for c in chunks]
        if corpus:
            self.bm25 = BM25Okapi(corpus)
        else:
            self.bm25 = None
        self.save_index()

    def keyword_search(
        self, 
        query: str, 
        top_k: int = 12, 
        filter_sources: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search using BM25.
        Returns:
            List of results with documents, metadata, scores, and ids.
        """
        if not self.bm25 or not self.chunks:
            return []

        query_tokens = tokenize(query)
        # Get raw BM25 scores
        scores = self.bm25.get_scores(query_tokens)
        
        results = []
        for idx, score in enumerate(scores):
            chunk = self.chunks[idx]
            
            # Apply source filtering if provided
            if filter_sources and chunk.source not in filter_sources:
                continue
                
            results.append({
                "chunk_id": chunk.chunk_id,
                "text": chunk.text,
                "metadata": {
                    "doc_id": chunk.doc_id,
                    "doc_hash": chunk.doc_hash,
                    "source": chunk.source,
                    "page_start": chunk.page_start,
                    "page_end": chunk.page_end,
                    "section": chunk.section or "",
                    "slide_number": chunk.slide_number or -1,
                    "chunk_sequence": chunk.chunk_sequence,
                    "timestamp": chunk.timestamp,
                    "access_category": chunk.access_category
                },
                "score": float(score)
            })

        # Sort by score descending and take top_k
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]
