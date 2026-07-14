import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    GROQ_API_KEY: Optional[str] = None
    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    EMBEDDING_MODEL: str = "BAAI/bge-small-en-v1.5"
    RERANKER_MODEL: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    DOCUMENT_DIRECTORY: str = "data"
    SAMPLE_DOCUMENT_DIRECTORY: str = "data/sample_documents"
    CHROMA_PERSIST_DIRECTORY: str = "data/chroma_db"
    BM25_INDEX_PATH: str = "data/processed/bm25_index.pkl"
    CHUNK_SIZE: int = 900
    CHUNK_OVERLAP: int = 150
    SEMANTIC_TOP_K: int = 6
    BM25_TOP_K: int = 6
    RERANK_TOP_K: int = 5
    MINIMUM_RERANK_SCORE: float = 0.20
    MAX_CONTEXT_CHARACTERS: int = 18000
    MAX_FILE_SIZE_MB: int = 25
    ENABLE_QUERY_REWRITING: bool = False
    ENABLE_LOGGING: bool = False
    LOG_LEVEL: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @property
    def doc_dir(self) -> Path:
        return Path(self.DOCUMENT_DIRECTORY)

    @property
    def sample_doc_dir(self) -> Path:
        return Path(self.SAMPLE_DOCUMENT_DIRECTORY)

    @property
    def chroma_persist_dir(self) -> Path:
        return Path(self.CHROMA_PERSIST_DIRECTORY)

    @property
    def bm25_index_path(self) -> Path:
        return Path(self.BM25_INDEX_PATH)

settings = Settings()
