import pytest
from src.indexing.index_manager import IndexManager
from src.retrieval.hybrid_retriever import HybridRetriever
from src.retrieval.rank_fusion import reciprocal_rank_fusion
from src.models.schemas import DocumentChunk

def test_rank_fusion():
    sem = [{"chunk_id": "c1", "text": "sem text"}, {"chunk_id": "c2", "text": "sem text 2"}]
    bm2 = [{"chunk_id": "c2", "text": "sem text 2"}, {"chunk_id": "c3", "text": "bm2 text"}]
    
    fused = reciprocal_rank_fusion(sem, bm2, k=60)
    assert len(fused) == 3
    # Check deduplication
    ids = [f["chunk_id"] for f in fused]
    assert len(set(ids)) == 3

@pytest.fixture
def index_manager():
    # Setup temporary index manager
    im = IndexManager()
    im.reset_all()
    
    # Ingest a few fake chunks
    chunks = [
        DocumentChunk(
            chunk_id="hash1_1_Sec1_0",
            doc_id="doc1",
            doc_hash="hash1",
            source="wellness_policy.md",
            text="The annual reimbursement limit for dental benefits is $500.",
            page_start=1,
            page_end=1,
            section="Dental Benefits",
            chunk_sequence=0,
            timestamp=123.45
        ),
        DocumentChunk(
            chunk_id="hash2_1_Sec2_0",
            doc_id="doc2",
            doc_hash="hash2",
            source="mental_health.md",
            text="Employees get up to 6 mental health counselling sessions per year.",
            page_start=1,
            page_end=1,
            section="Mental Health",
            chunk_sequence=0,
            timestamp=123.45
        )
    ]
    
    im.ingest_document_chunks("doc1", [chunks[0]])
    im.ingest_document_chunks("doc2", [chunks[1]])
    return im

def test_hybrid_retriever(index_manager):
    retriever = HybridRetriever(index_manager)
    
    # Test query that matches dental
    results = retriever.retrieve("dental reimbursement limit")
    assert len(results) > 0
    assert "Dental" in results[0]["metadata"]["section"]
    
    # Test query document filter
    filtered_results = retriever.retrieve("mental health sessions", filter_sources=["mental_health.md"])
    assert len(filtered_results) == 1
    assert filtered_results[0]["metadata"]["source"] == "mental_health.md"
