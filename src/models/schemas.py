from typing import List, Optional
from pydantic import BaseModel, Field

class DocumentChunk(BaseModel):
    chunk_id: str = Field(..., description="Stable chunk identifier: doc_hash + page + section + seq")
    doc_id: str = Field(..., description="Unique document ID (hash or name)")
    doc_hash: str = Field(..., description="SHA-256 hash of document")
    source: str = Field(..., description="Source filename")
    text: str = Field(..., description="Conservative-cleaned chunk text")
    page_start: int = Field(..., description="1-indexed starting page number")
    page_end: int = Field(..., description="1-indexed ending page number")
    slide_number: Optional[int] = Field(None, description="Optional slide number for PPTX")
    section: Optional[str] = Field(None, description="Section heading when available")
    paragraph_number: Optional[int] = Field(None, description="Optional paragraph number")
    chunk_sequence: int = Field(..., description="Sequential index of chunk in document")
    timestamp: float = Field(..., description="Ingestion timestamp")
    access_category: str = Field("confidential", description="Access restriction category")

class Citation(BaseModel):
    chunk_id: str = Field(..., description="Stable chunk identifier referencing the exact chunk")
    source: str = Field(..., description="Document filename matching the chunk")
    page_start: int = Field(..., description="Starting page number")
    page_end: int = Field(..., description="Ending page number")
    section: Optional[str] = Field("", description="Section heading or empty string if not available")
    quote: str = Field(..., description="Exact supporting quotation verified from the citation text")

class ChatbotResponse(BaseModel):
    answer_summary: str = Field(..., description="Clear grounded answer or summary")
    status: str = Field(..., description="answered | insufficient_evidence | conflicting_sources | safety_refusal")
    key_details: List[str] = Field(default_factory=list, description="Optional list of key details, conditions, exceptions")
    citations: List[Citation] = Field(default_factory=list, description="List of validated citations")
    confidence: str = Field(..., description="high | medium | low | insufficient | conflicting | safety_refusal")
    reason: str = Field(..., description="Brief explanation of evidence quality")
