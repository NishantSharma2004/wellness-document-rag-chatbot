import pytest
from src.preprocessing.chunker import StructureAwareChunker
from src.preprocessing.cleaner import TextCleaner

def test_cleaner():
    cleaner = TextCleaner()
    text = "Hello   World!\nThis is a hyphen-\nated word. \n\n\nNew line."
    cleaned = cleaner.clean(text)
    assert "Hello World!" in cleaned
    assert "hyphenated" in cleaned
    assert "\n\n" in cleaned
    assert "\n\n\n" not in cleaned

def test_structure_aware_chunker():
    chunker = StructureAwareChunker(chunk_size=100, chunk_overlap=20)
    
    pages = [
        {"text": "# Header 1\nThis is paragraph one of document.", "page_number": 1, "slide_number": None, "section": None},
        {"text": "This is paragraph two of document.", "page_number": 2, "slide_number": None, "section": None}
    ]
    
    chunks = chunker.chunk_document(
        pages=pages,
        doc_id="test_doc",
        doc_hash="abc123hash",
        source_name="test.md",
        timestamp=1234567.89
    )
    
    assert len(chunks) > 0
    # Check deterministic ID structure: hash + page + section + seq
    first_chunk = chunks[0]
    assert first_chunk.doc_hash == "abc123hash"
    assert first_chunk.source == "test.md"
    assert first_chunk.timestamp == 1234567.89
    assert first_chunk.chunk_id.startswith("abc123hash_1_Header1_")
    
    # Check overlap/preservation
    assert first_chunk.text != ""
