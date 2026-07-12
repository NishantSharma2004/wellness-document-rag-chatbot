import json
from typing import List, Dict, Any, Optional
from config.settings import settings
from src.indexing.index_manager import IndexManager
from src.retrieval.hybrid_retriever import HybridRetriever
from src.safety.guardrails import SafetyGuardrails
from src.safety.sanitization import sanitize_input, sanitize_output
from src.generation.groq_client import GroqClientManager
from src.generation.prompts import SYSTEM_PROMPT, format_context_items
from src.generation.citation_validator import CitationValidator
from src.models.schemas import ChatbotResponse, Citation
from src.utils.exceptions import GenerationException, CitationValidationError
from src.utils.logging_config import logger

class AnswerGenerator:
    def __init__(self, index_manager: IndexManager):
        self.index_manager = index_manager
        self.retriever = HybridRetriever(index_manager)
        self.guardrails = SafetyGuardrails()
        self.groq_client = GroqClientManager()
        self.citation_validator = CitationValidator()

    def generate_response(
        self, 
        query: str, 
        chat_history: Optional[List[Dict[str, str]]] = None,
        filter_sources: Optional[List[str]] = None
    ) -> ChatbotResponse:
        """
        Main pipeline coordinating Safety -> Retrieval -> Generation -> Citation Validation.
        """
        # 1. Sanitize & Guardrail Query
        cleaned_query = sanitize_input(query)
        if not cleaned_query:
            return ChatbotResponse(
                answer_summary="The query is empty or invalid.",
                status="insufficient_evidence",
                confidence="insufficient",
                reason="Empty query input."
            )

        is_safe, status, refusal_text = self.guardrails.validate_query(cleaned_query)
        if not is_safe:
            return ChatbotResponse(
                answer_summary=refusal_text,
                status=status,
                confidence="safety_refusal",
                reason="Query violated safety guidelines."
            )

        # 2. Hybrid Retrieval
        retrieved_chunks = self.retriever.retrieve(cleaned_query, filter_sources=filter_sources)
        
        # 3. Assess Evidence Sufficiency (If no chunks retrieved or below threshold)
        if not retrieved_chunks:
            return ChatbotResponse(
                answer_summary="I could not find sufficient information in the provided documents to answer this question. This assistant is restricted to the authorized company documents and does not use external information.",
                status="insufficient_evidence",
                confidence="insufficient",
                reason="No relevant document passages were retrieved."
            )

        # 4. Generate Grounded Response with Groq
        formatted_context = format_context_items(retrieved_chunks)
        user_prompt = f"CONTEXT:\n{formatted_context}\n\nUSER QUESTION:\n{cleaned_query}\n\nProvide response in JSON format matching the schema."
        
        try:
            raw_response = self.groq_client.call_llm(SYSTEM_PROMPT, user_prompt)
            # Parse into ChatbotResponse Pydantic model
            response_obj = ChatbotResponse(**raw_response)
        except Exception as e:
            logger.error(f"Failed to generate answer from Groq: {str(e)}")
            # Fallback to presenting retrieved chunks directly if LLM fails
            return ChatbotResponse(
                answer_summary="I encountered an issue generating the structured answer. Here are the top retrieved passages for your reference.",
                status="answered",
                key_details=[c["text"] for c in retrieved_chunks[:2]],
                confidence="low",
                reason=f"LLM call failed: {str(e)}"
            )

        # 5. Citation Validation
        is_valid, validated_citations = self.citation_validator.validate_citations(
            response_obj, 
            retrieved_chunks
        )

        if not is_valid:
            logger.info("Citation validation failed. Retrying generation with stricter warning...")
            # Retry once with stricter prompt warning
            strict_system = SYSTEM_PROMPT + "\n\nCRITICAL WARNING: Your previous attempt failed citation validation because you returned citations that did not exist exactly or had incorrect metadata. You MUST only cite chunk_ids and quotes that exist EXACTLY in the provided CONTEXT. NEVER invent or paraphrase quotes."
            try:
                raw_response = self.groq_client.call_llm(strict_system, user_prompt)
                response_obj = ChatbotResponse(**raw_response)
                is_valid, validated_citations = self.citation_validator.validate_citations(
                    response_obj, 
                    retrieved_chunks
                )
            except Exception as e:
                logger.error(f"Retry LLM call failed: {str(e)}")
                is_valid = False

            if not is_valid:
                logger.warning("Citation validation failed twice. Stripping quotes and providing warning.")
                # Show retrieved passages directly to user without citing hallucinated quotes
                # Clean up citations to avoid presenting fabricated quotes
                response_obj.citations = []
                response_obj.confidence = "low"
                response_obj.reason = "Citations could not be verified against source texts."
                
                # Append retrieved passages to key details as fallback
                fallback_details = ["Retrieved passage fallback: " + c["text"] for c in retrieved_chunks[:3]]
                response_obj.key_details.extend(fallback_details)
            else:
                response_obj.citations = validated_citations
        else:
            response_obj.citations = validated_citations

        # 6. Sanitize Output
        response_obj.answer_summary = sanitize_output(response_obj.answer_summary)
        response_obj.key_details = [sanitize_output(d) for d in response_obj.key_details]
        
        return response_obj
