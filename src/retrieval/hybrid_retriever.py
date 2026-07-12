from typing import List, Dict, Any, Optional
from config.settings import settings
from src.indexing.embeddings import LocalEmbeddingGenerator
from src.indexing.index_manager import IndexManager
from src.retrieval.rank_fusion import reciprocal_rank_fusion
from src.retrieval.reranker import LocalReranker
from src.utils.exceptions import RetrievalException

class HybridRetriever:
    def __init__(self, index_manager: IndexManager):
        self.index_manager = index_manager
        self.embedder = LocalEmbeddingGenerator()
        self.reranker = LocalReranker()

    def retrieve(
        self, 
        query: str, 
        filter_sources: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Execute hybrid retrieval:
        1. Semantic retrieval (ChromaDB)
        2. Keyword retrieval (BM25)
        3. Reciprocal Rank Fusion (RRF)
        4. CrossEncoder reranking
        """
        if not query.strip():
            return []

        try:
            # 1. Semantic Search
            query_embedding = self.embedder.get_query_embedding(query)
            semantic_results = self.index_manager.vector_store.semantic_search(
                query_embedding=query_embedding,
                top_k=settings.SEMANTIC_TOP_K,
                filter_sources=filter_sources
            )

            # 2. BM25 Search
            bm25_results = self.index_manager.bm25_store.keyword_search(
                query=query,
                top_k=settings.BM25_TOP_K,
                filter_sources=filter_sources
            )

            # 3. Reciprocal Rank Fusion (RRF)
            fused_results = reciprocal_rank_fusion(
                semantic_results=semantic_results,
                bm25_results=bm25_results,
                k=60
            )

            # 4. CrossEncoder Reranking
            reranked_results = self.reranker.rerank(
                query=query,
                items=fused_results,
                top_k=settings.RERANK_TOP_K
            )

            return reranked_results

        except Exception as e:
            raise RetrievalException(f"Hybrid retrieval failed: {str(e)}") from e
