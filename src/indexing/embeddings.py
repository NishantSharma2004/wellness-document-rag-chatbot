from typing import List
from sentence_transformers import SentenceTransformer
from config.settings import settings

class LocalEmbeddingGenerator:
    _model_instance = None

    @classmethod
    def get_model(cls) -> SentenceTransformer:
        if cls._model_instance is None:
            import torch
            # Optimize CPU threading for shared cloud instances (prevents CPU contention)
            if torch.get_num_threads() > 1:
                torch.set_num_threads(1)
            # Load the model locally and reuse it on CPU explicitly
            cls._model_instance = SentenceTransformer(settings.EMBEDDING_MODEL, device="cpu")
        return cls._model_instance

    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        model = self.get_model()
        # Sentence Transformers encodes to numpy array, we convert to list of floats
        embeddings = model.encode(texts, normalize_embeddings=True)
        return embeddings.tolist()

    def get_query_embedding(self, query: str) -> List[float]:
        model = self.get_model()
        embedding = model.encode(query, normalize_embeddings=True)
        return embedding.tolist()
