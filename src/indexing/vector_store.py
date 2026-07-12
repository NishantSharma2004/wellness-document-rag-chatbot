from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings as ChromaSettings
from config.settings import settings
from src.models.schemas import DocumentChunk
from src.utils.exceptions import IndexException
from src.utils.logging_config import logger

class VectorStoreManager:
    def __init__(self):
        try:
            self.client = chromadb.PersistentClient(
                path=settings.CHROMA_PERSIST_DIRECTORY,
                settings=ChromaSettings(anonymized_telemetry=False)
            )
            self.collection_name = "wellness_documents"
            # Get or create collection
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}  # BGE embeddings work well with cosine or l2 (cosine is normalized dot product)
            )
        except Exception as e:
            raise IndexException(f"Failed to initialize ChromaDB: {str(e)}") from e

    def add_chunks(self, chunks: List[DocumentChunk], embeddings: List[List[float]]) -> None:
        """Add chunks and their precomputed embeddings to ChromaDB."""
        if not chunks:
            return
        
        ids = [c.chunk_id for c in chunks]
        texts = [c.text for c in chunks]
        
        # Chroma metadata must be flat: strings, ints, floats, or bools
        metadatas = []
        for c in chunks:
            meta = {
                "doc_id": c.doc_id,
                "doc_hash": c.doc_hash,
                "source": c.source,
                "page_start": c.page_start,
                "page_end": c.page_end,
                "section": c.section or "",
                "slide_number": c.slide_number or -1,
                "chunk_sequence": c.chunk_sequence,
                "timestamp": c.timestamp,
                "access_category": c.access_category
            }
            metadatas.append(meta)

        try:
            self.collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=texts,
                metadatas=metadatas
            )
        except Exception as e:
            raise IndexException(f"Failed to add chunks to ChromaDB: {str(e)}") from e

    def delete_document(self, doc_id: str) -> None:
        """Delete all chunks belonging to a document ID."""
        try:
            self.collection.delete(where={"doc_id": doc_id})
        except Exception as e:
            raise IndexException(f"Failed to delete document {doc_id} from ChromaDB: {str(e)}") from e

    def semantic_search(
        self, 
        query_embedding: List[float], 
        top_k: int = 12, 
        filter_sources: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Execute semantic search.
        Returns:
            List of results with documents, metadatas, distances, and ids.
        """
        where = {}
        if filter_sources:
            if len(filter_sources) == 1:
                where = {"source": filter_sources[0]}
            else:
                where = {"$or": [{"source": src} for src in filter_sources]}

        try:
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=where if where else None
            )
            
            formatted_results = []
            if results and results["ids"] and results["ids"][0]:
                for idx in range(len(results["ids"][0])):
                    formatted_results.append({
                        "chunk_id": results["ids"][0][idx],
                        "text": results["documents"][0][idx],
                        "metadata": results["metadatas"][0][idx],
                        "score": 1.0 - results["distances"][0][idx]  # Convert distance to similarity
                    })
            return formatted_results
        except Exception as e:
            raise IndexException(f"ChromaDB search failed: {str(e)}") from e

    def list_documents(self) -> List[Dict[str, Any]]:
        """List unique documents and their metadata."""
        try:
            # We get all items to aggregate unique sources/hashes
            all_data = self.collection.get(include=["metadatas"])
            unique_docs = {}
            if all_data and all_data["metadatas"]:
                for meta in all_data["metadatas"]:
                    doc_id = meta["doc_id"]
                    if doc_id not in unique_docs:
                        unique_docs[doc_id] = {
                            "doc_id": doc_id,
                            "source": meta["source"],
                            "doc_hash": meta["doc_hash"],
                            "timestamp": meta["timestamp"]
                        }
            return list(unique_docs.values())
        except Exception as e:
            raise IndexException(f"Failed to list documents from ChromaDB: {str(e)}") from e

    def get_stats(self) -> Dict[str, Any]:
        """Return collection statistics."""
        try:
            count = self.collection.count()
            docs = self.list_documents()
            return {
                "total_chunks": count,
                "total_documents": len(docs),
                "documents": docs
            }
        except Exception as e:
            raise IndexException(f"Failed to get database stats: {str(e)}") from e

    def reset_collection(self) -> None:
        """Reset/clear the entire collection."""
        try:
            self.client.delete_collection(self.collection_name)
            self.collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}
            )
        except Exception as e:
            raise IndexException(f"Failed to reset collection: {str(e)}") from e
