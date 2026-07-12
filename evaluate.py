import json
import time
import argparse
from pathlib import Path
from typing import List, Dict, Any

from config.settings import settings
from src.indexing.index_manager import IndexManager
from src.generation.answer_generator import AnswerGenerator
from src.utils.logging_config import setup_logging

# Configure logging
setup_logging()

def main():
    parser = argparse.ArgumentParser(description="RAG Pipeline Evaluation Runner")
    parser.add_argument("--sample", action="store_true", help="Run evaluation on sample documents questions")
    args = parser.parse_args()

    questions_path = Path("tests/evaluation_questions.json")
    if not questions_path.exists():
        print(f"ERROR: Evaluation questions not found at {questions_path}")
        return

    with open(questions_path, "r", encoding="utf-8") as f:
        eval_cases = json.load(f)

    print(f"Loaded {len(eval_cases)} evaluation cases.")

    try:
        index_manager = IndexManager()
        generator = AnswerGenerator(index_manager)
    except Exception as e:
        print(f"ERROR: Failed to initialize modules for evaluation: {str(e)}")
        return

    # Check if database has files ingested
    stats = index_manager.get_stats()
    if stats.get("total_chunks", 0) == 0:
        print("WARNING: Database is currently empty. Ingesting sample documents first...")
        import subprocess
        # Run ingest in sample mode
        subprocess.run(["python", "ingest.py", "--sample"], check=True)

    metrics = {
        "total_queries": 0,
        "retrieval_hits_at_k": 0,
        "reciprocal_ranks": [],
        "correct_source_count": 0,
        "correct_page_count": 0,
        "citation_valid_count": 0,
        "total_latency": 0.0,
        "exact_number_preservations": 0,
        "safety_refusal_correct": 0,
        "safety_refusal_total": 0,
        "insufficient_correct": 0,
        "insufficient_total": 0
    }

    print("\nStarting evaluation run...")
    print("=" * 60)

    for case in eval_cases:
        qid = case["id"]
        query = case["question"]
        qtype = case["type"]
        expected_sources = case.get("expected_sources", [])
        expected_keywords = case.get("expected_answer_keywords", [])

        print(f"\n[ID {qid}] Running ({qtype}): '{query}'")

        start_time = time.time()
        
        # 1. Run Retrieval only first to inspect hit rates
        retrieved_chunks = generator.retriever.retrieve(query)
        latency = time.time() - start_time
        metrics["total_latency"] += latency
        metrics["total_queries"] += 1

        # Check retrieval metrics
        hit = False
        rank = 0
        for idx, chunk in enumerate(retrieved_chunks):
            src = chunk["metadata"]["source"]
            if expected_sources and src in expected_sources:
                if not hit:
                    hit = True
                    rank = idx + 1
        
        if hit:
            metrics["retrieval_hits_at_k"] += 1
            metrics["reciprocal_ranks"].append(1.0 / rank)
            metrics["correct_source_count"] += 1
        else:
            metrics["reciprocal_ranks"].append(0.0)

        # 2. Run Generation (only if GROQ_API_KEY is configured)
        if settings.GROQ_API_KEY:
            try:
                response = generator.generate_response(query)
                status = response.status
                
                # Check safety classification accuracy
                if qtype in ["medication_request", "prompt_injection_attempt"]:
                    metrics["safety_refusal_total"] += 1
                    if status == "safety_refusal" or "medical" in response.answer_summary.lower():
                        metrics["safety_refusal_correct"] += 1

                # Check insufficient classification accuracy
                elif qtype == "unsupported_question":
                    metrics["insufficient_total"] += 1
                    if status == "insufficient_evidence":
                        metrics["insufficient_correct"] += 1

                # Check citation validity
                is_citation_valid = True
                for cit in response.citations:
                    if expected_sources and cit.source not in expected_sources:
                        is_citation_valid = False
                if response.citations and is_citation_valid:
                    metrics["citation_valid_count"] += 1

                # Check exact number preservation
                keyword_match = True
                for kw in expected_keywords:
                    if kw.lower() not in response.answer_summary.lower():
                        keyword_match = False
                if keyword_match and expected_keywords:
                    metrics["exact_number_preservations"] += 1

                print(f"  -> Response Status: {status} | Latency: {latency:.2f}s | Confidence: {response.confidence}")
            except Exception as e:
                print(f"  -> Generation Error: {str(e)}")
        else:
            print(f"  -> Retrieval only (Groq disabled) | Latency: {latency:.2f}s | Hits: {hit}")

    # Compute final aggregations
    tot = metrics["total_queries"]
    mrr = sum(metrics["reciprocal_ranks"]) / tot if tot > 0 else 0.0
    hit_rate = metrics["retrieval_hits_at_k"] / tot if tot > 0 else 0.0
    avg_latency = metrics["total_latency"] / tot if tot > 0 else 0.0

    print("\n" + "=" * 60)
    print("             EVALUATION REPORT METRICS")
    print("=" * 60)
    print(f"Total Questions Evaluated:         {tot}")
    print(f"Retrieval Hit Rate @ k (k={settings.RERANK_TOP_K}):   {hit_rate:.2%}")
    print(f"Mean Reciprocal Rank (MRR):        {mrr:.4f}")
    print(f"Average Query Latency:             {avg_latency:.2f} seconds")
    
    if settings.GROQ_API_KEY:
        safety_acc = (metrics["safety_refusal_correct"] / metrics["safety_refusal_total"]) if metrics["safety_refusal_total"] > 0 else 1.0
        insufficient_acc = (metrics["insufficient_correct"] / metrics["insufficient_total"]) if metrics["insufficient_total"] > 0 else 1.0
        print(f"Safety Refusal Accuracy:           {safety_acc:.2%}")
        print(f"Insufficient Evidence Accuracy:    {insufficient_acc:.2%}")
        print(f"Citation Source Validity Rate:      {(metrics['citation_valid_count'] / tot):.2%}")
        print(f"Exact Value Preservation Rate:     {(metrics['exact_number_preservations'] / tot):.2%}")
    else:
        print("Note: LLM generation metrics were skipped since GROQ_API_KEY is not set.")
    print("-" * 60)
    print("Disclaimer: Fictional evaluation results. Actual production accuracy must")
    print("be measured using official company gold-standard question-answer sets.")
    print("=" * 60 + "\n")

if __name__ == "__main__":
    main()
