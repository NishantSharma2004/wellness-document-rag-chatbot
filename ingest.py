import sys
import argparse
import time
from pathlib import Path
from typing import List, Dict, Any

from config.settings import settings
from src.utils.hashing import calculate_file_hash
from src.utils.logging_config import setup_logging
from src.utils.exceptions import ChatbotException
from src.loaders.pdf_loader import PDFLoader
from src.loaders.docx_loader import DocxLoader
from src.loaders.pptx_loader import PptxLoader
from src.loaders.text_loader import TextLoader
from src.preprocessing.cleaner import TextCleaner
from src.preprocessing.chunker import StructureAwareChunker
from src.indexing.index_manager import IndexManager

# Configure logging
setup_logging()

def get_loader(filepath: Path):
    ext = filepath.suffix.lower()
    if ext == ".pdf":
        return PDFLoader()
    elif ext == ".docx":
        return DocxLoader()
    elif ext == ".pptx":
        return PptxLoader()
    elif ext in [".txt", ".md"]:
        return TextLoader()
    else:
        return None

def main():
    parser = argparse.ArgumentParser(description="Wellness Document Ingestion Pipeline")
    parser.add_argument("--sample", action="store_true", help="Ingest only fictional sample documents")
    parser.add_argument("--reset", action="store_true", help="Reset/clear database before ingestion")
    args = parser.parse_args()

    start_time = time.time()
    
    # Target directory selection
    if args.sample:
        doc_dir = Path(settings.SAMPLE_DOCUMENT_DIRECTORY)
        print(f"Ingesting SAMPLE documents from: {doc_dir}")
    else:
        doc_dir = Path(settings.DOCUMENT_DIRECTORY)
        print(f"Ingesting PRODUCTION documents from: {doc_dir}")

    if not doc_dir.exists():
        doc_dir.mkdir(parents=True, exist_ok=True)
        # Create a placeholder or README if production
        if not args.sample:
            with open(doc_dir / "README.md", "w") as f:
                f.write("# Production Documents Directory\nPlace all official company healthcare and wellness policies here.\n")

    try:
        index_manager = IndexManager()
    except Exception as e:
        print(f"ERROR: Failed to initialize Index Manager: {str(e)}")
        sys.exit(1)

    if args.reset:
        print("Resetting database collection...")
        index_manager.reset_all()

    # Discover files
    supported_extensions = {".pdf", ".docx", ".pptx", ".txt", ".md"}
    all_files = [p for p in doc_dir.iterdir() if p.is_file() and p.suffix.lower() in supported_extensions]

    # Report structure
    report = {
        "discovered": len(all_files),
        "processed": 0,
        "skipped": 0,
        "failed": [],
        "pages_extracted": 0,
        "slides_extracted": 0,
        "chunks_created": 0,
        "duplicates_removed": 0,
        "ocr_needed_pages": 0,
    }

    # Fetch current documents already in DB
    existing_docs = {d["doc_id"]: d for d in index_manager.get_indexed_documents()}
    
    cleaner = TextCleaner()
    chunker = StructureAwareChunker(chunk_size=settings.CHUNK_SIZE, chunk_overlap=settings.CHUNK_OVERLAP)

    for filepath in all_files:
        doc_id = filepath.name
        try:
            # 1. Compute Hash
            file_hash = calculate_file_hash(filepath)
            
            # 2. Check if unchanged
            if doc_id in existing_docs and existing_docs[doc_id]["doc_hash"] == file_hash:
                report["skipped"] += 1
                continue
                
            # 3. Load & Extract
            loader = get_loader(filepath)
            if not loader:
                report["failed"].append((filepath.name, "No compatible loader found"))
                continue
                
            pages = loader.load(filepath)
            if not pages:
                report["failed"].append((filepath.name, "No content extracted"))
                continue

            # Update stats
            is_pptx = filepath.suffix.lower() == ".pptx"
            if is_pptx:
                report["slides_extracted"] += len(pages)
            else:
                report["pages_extracted"] += len(pages)

            # 4. Clean & Chunk page text
            cleaned_pages = []
            for p in pages:
                cleaned_text = cleaner.clean(p["text"])
                
                # Scanned page detection logic check
                if len(cleaned_text) < 15:
                    report["ocr_needed_pages"] += 1
                    
                cleaned_pages.append({
                    "text": cleaned_text,
                    "page_number": p["page_number"],
                    "slide_number": p["slide_number"],
                    "section": p["section"]
                })

            # Chunk document
            timestamp = time.time()
            chunks = chunker.chunk_document(
                pages=cleaned_pages,
                doc_id=doc_id,
                doc_hash=file_hash,
                source_name=filepath.name,
                timestamp=timestamp
            )
            
            # We track chunk stats
            report["chunks_created"] += len(chunks)

            # 5. Ingest chunks
            index_manager.ingest_document_chunks(doc_id, chunks)
            report["processed"] += 1

        except Exception as e:
            report["failed"].append((filepath.name, str(e)))
            print(f"Failed to process {filepath.name}: {str(e)}")

    # Sync BM25 at the end in case something changed
    if report["processed"] > 0:
        index_manager.sync_bm25_from_vector_store()

    # Print Report
    elapsed_time = time.time() - start_time
    print("\n" + "="*50)
    print("           DOCUMENT INGESTION REPORT")
    print("="*50)
    print(f"Files Discovered:         {report['discovered']}")
    print(f"Files Processed:          {report['processed']}")
    print(f"Files Skipped (Unchanged): {report['skipped']}")
    print(f"Files Failed:             {len(report['failed'])}")
    if report["failed"]:
        for name, err in report["failed"]:
            print(f"  - {name}: {err}")
    print("-"*50)
    print(f"Pages Extracted:          {report['pages_extracted']}")
    print(f"Slides Extracted:         {report['slides_extracted']}")
    print(f"Chunks Created:           {report['chunks_created']}")
    print(f"Pages Needing OCR:        {report['ocr_needed_pages']}")
    print(f"Total Processing Time:    {elapsed_time:.2f} seconds")
    print("="*50 + "\n")

    if len(report["failed"]) > 0 and report["processed"] == 0:
        sys.exit(1)
        
    sys.exit(0)

if __name__ == "__main__":
    main()
