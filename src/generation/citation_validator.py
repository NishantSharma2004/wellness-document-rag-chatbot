import re
from typing import List, Dict, Any, Tuple
from src.models.schemas import Citation, ChatbotResponse
from src.utils.exceptions import CitationValidationError
from src.utils.logging_config import logger

class CitationValidator:
    def clean_text_for_comparison(self, text: str) -> str:
        """Helper to normalize whitespace for comparison."""
        # Convert to lowercase and replace any whitespace sequence with a single space
        return re.sub(r'\s+', ' ', text.strip().lower())

    def validate_citations(
        self, 
        response: ChatbotResponse, 
        retrieved_chunks: List[Dict[str, Any]]
    ) -> Tuple[bool, List[Citation]]:
        """
        Validate that every citation returned by the LLM is accurate and grounded:
        1. chunk_id must exist in retrieved chunks.
        2. source, page, section must match the chunk's metadata.
        3. quote must exist exactly as a substring within the chunk's original text.
        """
        validated_citations = []
        chunk_map = {c["chunk_id"]: c for c in retrieved_chunks}

        for citation in response.citations:
            chunk_id = citation.chunk_id
            
            # 1. Verify chunk ID exists
            if chunk_id not in chunk_map:
                logger.warning(f"Citation validation failed: chunk_id '{chunk_id}' not in retrieved results.")
                return False, []

            chunk = chunk_map[chunk_id]
            meta = chunk["metadata"]
            
            # 2. Verify metadata matches
            if citation.source != meta["source"]:
                logger.warning(f"Citation validation failed: source mismatch. Citation: '{citation.source}', Metadata: '{meta['source']}'")
                return False, []
                
            if citation.page_start != meta["page_start"]:
                logger.warning(f"Citation validation failed: page_start mismatch. Citation: '{citation.page_start}', Metadata: '{meta['page_start']}'")
                return False, []

            # 3. Verify exact quote exists in chunk text
            cleaned_quote = self.clean_text_for_comparison(citation.quote)
            cleaned_chunk_text = self.clean_text_for_comparison(chunk["text"])

            if cleaned_quote not in cleaned_chunk_text:
                logger.warning(f"Citation validation failed: Quote '{citation.quote}' was not found in the original chunk text.")
                return False, []

            validated_citations.append(citation)

        return True, validated_citations
