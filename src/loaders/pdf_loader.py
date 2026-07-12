from pathlib import Path
from typing import List, Dict, Any
import fitz  # PyMuPDF
from src.loaders.base import BaseLoader
from src.utils.exceptions import LoaderException
from src.utils.logging_config import logger

class PDFLoader(BaseLoader):
    def load(self, filepath: Path) -> List[Dict[str, Any]]:
        self.validate_file(filepath)
        
        pages = []
        scanned_pages = []
        
        try:
            doc = fitz.open(filepath)
            for page_idx, page in enumerate(doc):
                page_num = page_idx + 1
                text = page.get_text()
                
                # Check for likely scanned page
                clean_text = text.strip()
                # If page is empty or text is extremely short, check if it contains images
                is_scanned = False
                if len(clean_text) < 15:
                    image_list = page.get_images()
                    if image_list or len(clean_text) == 0:
                        is_scanned = True
                
                if is_scanned:
                    scanned_pages.append(page_num)
                
                pages.append({
                    "text": text,
                    "page_number": page_num,
                    "slide_number": None,
                    "section": None
                })
            doc.close()
        except Exception as e:
            raise LoaderException(f"Failed to load PDF file {filepath}: {str(e)}") from e
        
        if scanned_pages:
            warning_msg = f"OCR may be required for pages {', '.join(map(str, scanned_pages))} in {filepath.name}."
            logger.warning(warning_msg)
            # Store scanned page warning or print it
            print(f"WARNING: {warning_msg}")
            
        return pages
