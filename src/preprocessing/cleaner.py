import re
import unicodedata
from src.utils.exceptions import CleanException

class TextCleaner:
    def clean(self, text: str) -> str:
        """
        Perform conservative cleaning on extracted text.
        """
        if not text:
            return ""
        
        try:
            # 1. Unicode normalization (NFKC)
            text = unicodedata.normalize("NFKC", text)
            
            # 2. Dehyphenation of words broken across lines (e.g. wellness-\nleave -> wellnessleave)
            text = re.sub(r'(\w+)-\n\s*(\w+)', r'\1\2', text)
            
            # 3. Standardize newlines
            text = text.replace('\r\n', '\n').replace('\r', '\n')
            
            # 4. Whitespace normalization per line
            # Keep line structure but compress consecutive spaces/tabs
            lines = []
            for line in text.split('\n'):
                cleaned_line = re.sub(r'[ \t]+', ' ', line).strip()
                lines.append(cleaned_line)
            
            # 5. Blank-line normalization (max 2 consecutive blank lines)
            cleaned_text = '\n'.join(lines)
            cleaned_text = re.sub(r'\n{3,}', '\n\n', cleaned_text)
            
            return cleaned_text.strip()
            
        except Exception as e:
            raise CleanException(f"Text cleaning failed: {str(e)}") from e
