import re
from typing import List, Dict, Any
from src.models.schemas import DocumentChunk
from src.utils.exceptions import ChunkException

class StructureAwareChunker:
    def __init__(self, chunk_size: int = 900, chunk_overlap: int = 150):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk_document(
        self, 
        pages: List[Dict[str, Any]], 
        doc_id: str, 
        doc_hash: str, 
        source_name: str,
        timestamp: float
    ) -> List[DocumentChunk]:
        """
        Chunks list of pages while preserving structure and headings.
        """
        chunks = []
        chunk_sequence = 0
        current_section = "General"
        
        # We process paragraph-by-paragraph across pages, keeping track of page numbers
        paragraphs = []
        for p in pages:
            text = p["text"]
            page_num = p["page_number"]
            slide_num = p["slide_number"]
            
            # Split text into paragraphs (lines separated by double newlines or single newlines with headings)
            lines = text.split("\n")
            current_paragraph = []
            
            for line in lines:
                line_str = line.strip()
                if not line_str:
                    if current_paragraph:
                        paragraphs.append({
                            "text": " ".join(current_paragraph),
                            "page": page_num,
                            "slide": slide_num
                        })
                        current_paragraph = []
                    continue
                
                # Check for heading
                is_heading = False
                # Markdown headers or capital short lines
                if line_str.startswith("#") or (line_str.isupper() and len(line_str) < 60) or re.match(r'^(Section|Policy|Article|Chapter)\s+\d+', line_str, re.IGNORECASE):
                    is_heading = True
                
                if is_heading:
                    # Flush current paragraph first
                    if current_paragraph:
                        paragraphs.append({
                            "text": " ".join(current_paragraph),
                            "page": page_num,
                            "slide": slide_num
                        })
                        current_paragraph = []
                    # Add heading itself as a paragraph
                    paragraphs.append({
                        "text": line_str,
                        "page": page_num,
                        "slide": slide_num,
                        "is_heading": True
                    })
                else:
                    current_paragraph.append(line_str)
            
            if current_paragraph:
                paragraphs.append({
                    "text": " ".join(current_paragraph),
                    "page": page_num,
                    "slide": slide_num
                })

        # Now group paragraphs into chunks
        current_chunk_paragraphs = []
        current_chunk_len = 0
        start_page = 1
        current_slide = None
        
        # Dedup check helper
        seen_texts = set()

        for idx, para in enumerate(paragraphs):
            para_text = para["text"]
            para_page = para["page"]
            para_slide = para["slide"]
            is_head = para.get("is_heading", False)
            
            if is_head:
                current_section = para_text.lstrip("# ").strip()
            
            # If current chunk has paragraphs and adding this exceeds chunk_size, we write out the chunk
            if current_chunk_paragraphs and (current_chunk_len + len(para_text) > self.chunk_size):
                chunk_text = "\n".join([p["text"] for p in current_chunk_paragraphs])
                
                # Deduplication check
                if chunk_text.strip() not in seen_texts:
                    seen_texts.add(chunk_text.strip())
                    
                    end_page = current_chunk_paragraphs[-1]["page"]
                    
                    # Generate deterministic chunk ID
                    # hash + page + section + seq
                    # Sanitise section for inclusion in ID
                    safe_sec = re.sub(r'[^a-zA-Z0-9]', '', current_section)[:15]
                    chunk_id = f"{doc_hash}_{start_page}_{safe_sec}_{chunk_sequence}"
                    
                    chunks.append(DocumentChunk(
                        chunk_id=chunk_id,
                        doc_id=doc_id,
                        doc_hash=doc_hash,
                        source=source_name,
                        text=chunk_text,
                        page_start=start_page,
                        page_end=end_page,
                        slide_number=current_slide,
                        section=current_section,
                        paragraph_number=None,
                        chunk_sequence=chunk_sequence,
                        timestamp=timestamp,
                        access_category="confidential"
                    ))
                    chunk_sequence += 1
                
                # Apply overlap by keeping last paragraph(s) if size allows
                overlap_paras = []
                overlap_len = 0
                for op in reversed(current_chunk_paragraphs):
                    if overlap_len + len(op["text"]) < self.chunk_overlap:
                        overlap_paras.insert(0, op)
                        overlap_len += len(op["text"])
                    else:
                        break
                current_chunk_paragraphs = overlap_paras
                current_chunk_len = overlap_len
                if current_chunk_paragraphs:
                    start_page = current_chunk_paragraphs[0]["page"]
                    current_slide = current_chunk_paragraphs[0]["slide"]
                else:
                    start_page = para_page
                    current_slide = para_slide
            
            if not current_chunk_paragraphs:
                start_page = para_page
                current_slide = para_slide
                
            current_chunk_paragraphs.append(para)
            current_chunk_len += len(para_text)

        # Flush remaining paragraphs
        if current_chunk_paragraphs:
            chunk_text = "\n".join([p["text"] for p in current_chunk_paragraphs])
            if chunk_text.strip() not in seen_texts:
                end_page = current_chunk_paragraphs[-1]["page"]
                safe_sec = re.sub(r'[^a-zA-Z0-9]', '', current_section)[:15]
                chunk_id = f"{doc_hash}_{start_page}_{safe_sec}_{chunk_sequence}"
                
                chunks.append(DocumentChunk(
                    chunk_id=chunk_id,
                    doc_id=doc_id,
                    doc_hash=doc_hash,
                    source=source_name,
                    text=chunk_text,
                    page_start=start_page,
                    page_end=end_page,
                    slide_number=current_slide,
                    section=current_section,
                    paragraph_number=None,
                    chunk_sequence=chunk_sequence,
                    timestamp=timestamp,
                    access_category="confidential"
                ))
                
        return chunks
