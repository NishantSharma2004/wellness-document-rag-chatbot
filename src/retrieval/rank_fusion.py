from typing import List, Dict, Any

def reciprocal_rank_fusion(
    semantic_results: List[Dict[str, Any]], 
    bm25_results: List[Dict[str, Any]], 
    k: int = 60
) -> List[Dict[str, Any]]:
    """
    Perform Reciprocal Rank Fusion (RRF) on semantic and BM25 search results.
    Args:
        semantic_results: List of search results from ChromaDB query.
        bm25_results: List of search results from BM25.
        k: RRF constant parameter (default 60).
    """
    rrf_scores = {}
    item_map = {}

    # Rank 1-indexed
    # 1. Semantic ranks
    for rank, item in enumerate(semantic_results, start=1):
        chunk_id = item["chunk_id"]
        rrf_scores[chunk_id] = rrf_scores.get(chunk_id, 0.0) + (1.0 / (k + rank))
        if chunk_id not in item_map:
            item_map[chunk_id] = item

    # 2. BM25 ranks
    for rank, item in enumerate(bm25_results, start=1):
        chunk_id = item["chunk_id"]
        rrf_scores[chunk_id] = rrf_scores.get(chunk_id, 0.0) + (1.0 / (k + rank))
        if chunk_id not in item_map:
            item_map[chunk_id] = item

    # Sort items based on computed RRF scores
    sorted_ids = sorted(rrf_scores.keys(), key=lambda x: rrf_scores[x], reverse=True)
    
    fused_results = []
    for chunk_id in sorted_ids:
        item = item_map[chunk_id].copy()
        # Annotate item with rrf score
        item["rrf_score"] = rrf_scores[chunk_id]
        fused_results.append(item)
        
    return fused_results
