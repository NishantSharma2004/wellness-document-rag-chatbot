import re
from pathlib import Path
from typing import List, Dict, Any
from src.loaders.base import BaseLoader
from src.utils.exceptions import LoaderException

class TextLoader(BaseLoader):
    def load(self, filepath: Path) -> List[Dict[str, Any]]:
        self.validate_file(filepath)
        
        pages = []
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            
            # For Markdown or Text, we can split on `---` or form feed `\f`
            # or split on major headers like `# ` if markdown.
            # Let's check if there are markdown sections.
            if filepath.suffix.lower() == ".md" and "---" in content:
                # split by markdown page breaks (often represented by --- on a line by itself)
                sections = re.split(r'\n---\n', content)
                for idx, sec in enumerate(sections):
                    pages.append({
                        "text": sec,
                        "page_number": idx + 1,
                        "slide_number": None,
                        "section": None
                    })
            else:
                # Default character chunking to simulate pages for txt
                char_limit = 2500
                page_num = 1
                for i in range(0, len(content), char_limit):
                    pages.append({
                        "text": content[i : i + char_limit],
                        "page_number": page_num,
                        "slide_number": None,
                        "section": None
                    })
                    page_num += 1
        except Exception as e:
            raise LoaderException(f"Failed to load text/markdown file {filepath}: {str(e)}") from e
            
        return pages
