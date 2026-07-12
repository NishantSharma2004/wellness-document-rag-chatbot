from typing import List, Dict, Any
from sentence_transformers import CrossEncoder
from config.settings import settings

class LocalReranker:
    _model_instance = None

    @classmethod
    def get_model(cls) -> CrossEncoder:
        if cls._model_instance is None:
            # Load the CrossEncoder model once
            cls._model_instance = CrossEncoder(settings.RERANKER_MODEL)
        return cls._model_instance

    def rerank(self, query: str, items: List[Dict[str, Any]], top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Rerank a list of retrieved chunks using CrossEncoder.
        Returns:
            Sorted and pruned list of items containing 'rerank_score'.
        """
        if not items:
            return []

        model = self.get_model()
        pairs = [[query, item["text"]] for item in items]
        
        # Predict scores
        scores = model.predict(pairs)
        
        reranked_items = []
        for idx, score in enumerate(scores):
            item = items[idx].copy()
            # In MS-Marco models, scores are logits (e.g. -10 to +10). We can convert
            # to a sigmoid if we want a 0-1 probability, but using direct float scores is standard.
            # However, the settings define a MINIMUM_RERANK_SCORE. If it is 0.20, let's normalize or use raw score.
            # Standard CrossEncoder for MS-Marco outputs logits. 
            # Often, we apply sigmoid to score: 1 / (1 + exp(-score)). Let's check.
            # Yes, mapping logits to [0, 1] using sigmoid is cleaner for the minimum score filter.
            import math
            probability = 1.0 / (1.0 + math.exp(-float(score)))
            item["rerank_score"] = probability
            reranked_items.append(item)

        # Sort and filter
        reranked_items.sort(key=lambda x: x["rerank_score"], reverse=True)
        
        # Filter by minimum score threshold
        filtered_items = [
            item for item in reranked_items 
            if item["rerank_score"] >= settings.MINIMUM_RERANK_SCORE
        ]
        
        return filtered_items[:top_k]
