import pytest
from src.generation.citation_validator import CitationValidator
from src.models.schemas import ChatbotResponse, Citation

def test_citation_validator_success():
    validator = CitationValidator()
    
    retrieved = [
        {
            "chunk_id": "c1",
            "text": "The annual reimbursement limit for dental benefits is $500.",
            "metadata": {
                "source": "wellness_policy.md",
                "page_start": 1,
                "page_end": 1,
                "section": "Dental"
            }
        }
    ]
    
    response = ChatbotResponse(
        answer_summary="The limit is $500.",
        status="answered",
        citations=[
            Citation(
                chunk_id="c1",
                source="wellness_policy.md",
                page_start=1,
                page_end=1,
                section="Dental",
                quote="dental benefits is $500"
            )
        ],
        confidence="high",
        reason="Matched"
    )
    
    is_valid, validated = validator.validate_citations(response, retrieved)
    assert is_valid is True
    assert len(validated) == 1

def test_citation_validator_wrong_id():
    validator = CitationValidator()
    
    retrieved = [
        {
            "chunk_id": "c1",
            "text": "Test text",
            "metadata": {"source": "doc.md", "page_start": 1, "page_end": 1, "section": "Sec"}
        }
    ]
    
    response = ChatbotResponse(
        answer_summary="Summary",
        status="answered",
        citations=[
            Citation(
                chunk_id="c2",  # Wrong ID
                source="doc.md",
                page_start=1,
                page_end=1,
                section="Sec",
                quote="Test text"
            )
        ],
        confidence="high",
        reason="Matched"
    )
    
    is_valid, validated = validator.validate_citations(response, retrieved)
    assert is_valid is False

def test_citation_validator_wrong_quote():
    validator = CitationValidator()
    
    retrieved = [
        {
            "chunk_id": "c1",
            "text": "Test text",
            "metadata": {"source": "doc.md", "page_start": 1, "page_end": 1, "section": "Sec"}
        }
    ]
    
    response = ChatbotResponse(
        answer_summary="Summary",
        status="answered",
        citations=[
            Citation(
                chunk_id="c1",
                source="doc.md",
                page_start=1,
                page_end=1,
                section="Sec",
                quote="invented quote"  # Hallucinated quote
            )
        ],
        confidence="high",
        reason="Matched"
    )
    
    is_valid, validated = validator.validate_citations(response, retrieved)
    assert is_valid is False
