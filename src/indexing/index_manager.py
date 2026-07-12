from typing import List, Dict, Any, Tuple
from src.indexing.vector_store import VectorStoreManager
from src.indexing.bm25_store import BM25StoreManager
from src.indexing.embeddings import LocalEmbeddingGenerator
from src.models.schemas import DocumentChunk
from src.utils.exceptions import IndexException
from src.utils.logging_config import logger

class IndexManager:
    def __init__(self):
        self.vector_store = VectorStoreManager()
        self.bm25_store = BM25StoreManager()
        self.embedder = LocalEmbeddingGenerator()

    def get_indexed_documents(self) -> List[Dict[str, Any]]:
        """List unique documents and their metadata."""
        return self.vector_store.list_documents()

    def delete_document(self, doc_id: str) -> None:
        """Remove a document from both stores and rebuild BM25."""
        logger.info(f"Deleting document {doc_id} from indices...")
        self.vector_store.delete_document(doc_id)
        self.sync_bm25_from_vector_store()

    def ingest_document_chunks(self, doc_id: str, chunks: List[DocumentChunk]) -> None:
        """
        Ingests document chunks:
        1. Deletes old document version from Chroma.
        2. Computes embeddings.
        3. Saves new chunks to Chroma.
        4. Rebuilds BM25 index.
        """
        if not chunks:
            # If doc is empty, delete it
            self.delete_document(doc_id)
            return

        logger.info(f"Ingesting {len(chunks)} chunks for document {doc_id}...")
        
        # 1. Delete old chunks
        self.vector_store.delete_document(doc_id)

        # 2. Compute embeddings (batching for performance/memory safety)
        texts = [c.text for c in chunks]
        embeddings = self.embedder.get_embeddings(texts)

        # 3. Add to Chroma
        self.vector_store.add_chunks(chunks, embeddings)

        # 4. Sync and rebuild BM25 from the current collection chunks
        self.sync_bm25_from_vector_store()

    def sync_bm25_from_vector_store(self) -> None:
        """
        Fetch all chunks from ChromaDB, reconstruct DocumentChunk schemas,
        and rebuild the persistent BM25 index.
        """
        logger.info("Syncing BM25 index from ChromaDB...")
        try:
            # Fetch all items from chroma with documents and metadatas
            all_items = self.vector_store.collection.get(include=["documents", "metadatas"])
            chunks = []
            
            if all_items and all_items["ids"]:
                for idx in range(len(all_items["ids"])):
                    meta = all_items["metadatas"][idx]
                    chunks.append(DocumentChunk(
                        chunk_id=all_items["ids"][idx],
                        doc_id=meta["doc_id"],
                        doc_hash=meta["doc_hash"],
                        source=meta["source"],
                        text=all_items["documents"][idx],
                        page_start=meta["page_start"],
                        page_end=meta["page_end"],
                        slide_number=meta["slide_number"] if meta.get("slide_number") != -1 else None,
                        section=meta["section"] if meta.get("section") else None,
                        paragraph_number=None,
                        chunk_sequence=meta["chunk_sequence"],
                        timestamp=meta["timestamp"],
                        access_category=meta.get("access_category", "confidential")
                    ))
            
            # Rebuild and save BM25 index
            self.bm25_store.build_index(chunks)
            logger.info(f"Sync complete. BM25 indexed {len(chunks)} chunks.")
        except Exception as e:
            raise IndexException(f"Failed to sync BM25 from Vector Store: {str(e)}") from e

    def get_stats(self) -> Dict[str, Any]:
        """Return metrics on ingestion status."""
        return self.vector_store.get_stats()

    def reset_all(self) -> None:
        """Reset database and clear indexes."""
        logger.warning("Resetting both vector and BM25 stores...")
        self.vector_store.reset_collection()
        self.bm25_store.build_index([])
