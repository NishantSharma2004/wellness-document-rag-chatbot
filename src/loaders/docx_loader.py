from pathlib import Path
from typing import List, Dict, Any
import docx
from src.loaders.base import BaseLoader
from src.utils.exceptions import LoaderException

class DocxLoader(BaseLoader):
    def load(self, filepath: Path) -> List[Dict[str, Any]]:
        self.validate_file(filepath)
        
        pages = []
        try:
            doc = docx.Document(filepath)
            
            # Simple text extraction. We can group paragraphs into "pages" roughly by text length
            # or treat each heading/section as a page.
            # Let's accumulate text and create a new "page" every 2500 characters.
            current_text = []
            char_count = 0
            page_num = 1
            
            # Helper to check if a paragraph is a heading
            def is_heading(p):
                return p.style.name.startswith("Heading")

            # Extract both paragraphs and tables if possible
            for element in doc.element.body:
                if element.tag.endswith('p'):
                    p = docx.text.paragraph.Paragraph(element, doc)
                    p_text = p.text.strip()
                    if not p_text:
                        continue
                    
                    current_text.append(p_text + "\n")
                    char_count += len(p_text)
                    
                    # Split page if character count exceeds 2500
                    if char_count > 2500:
                        pages.append({
                            "text": "".join(current_text),
                            "page_number": page_num,
                            "slide_number": None,
                            "section": None  # We can parse heading if needed in chunker
                        })
                        current_text = []
                        char_count = 0
                        page_num += 1
                elif element.tag.endswith('tbl'):
                    t = docx.table.Table(element, doc)
                    t_text = []
                    for row in t.rows:
                        row_text = [cell.text.strip() for cell in row.cells]
                        t_text.append(" | ".join(row_text))
                    t_str = "\n".join(t_text) + "\n"
                    current_text.append(t_str)
                    char_count += len(t_str)
            
            # Add remaining text
            if current_text or not pages:
                pages.append({
                    "text": "".join(current_text),
                    "page_number": page_num,
                    "slide_number": None,
                    "section": None
                })
                
        except Exception as e:
            raise LoaderException(f"Failed to load DOCX file {filepath}: {str(e)}") from e
            
        return pages
