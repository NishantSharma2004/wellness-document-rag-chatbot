import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Dict, Any
from config.settings import settings
from src.utils.exceptions import LoaderException

class BaseLoader(ABC):
    @abstractmethod
    def load(self, filepath: Path) -> List[Dict[str, Any]]:
        """
        Load a document and extract page-level text and metadata.
        Returns:
            List of dicts: [
                {
                    "text": str,
                    "page_number": int,
                    "slide_number": Optional[int],
                    "section": Optional[str]
                }
            ]
        """
        pass

    def validate_file(self, filepath: Path) -> None:
        """Standard file validation validation."""
        if not filepath.exists():
            raise LoaderException(f"File not found: {filepath}")
        if not filepath.is_file():
            raise LoaderException(f"Path is not a file: {filepath}")
        
        # Check file size
        file_size_mb = filepath.stat().st_size / (1024 * 1024)
        if file_size_mb > settings.MAX_FILE_SIZE_MB:
            raise LoaderException(
                f"File size {file_size_mb:.2f}MB exceeds limit of {settings.MAX_FILE_SIZE_MB}MB"
            )
        
        # Check empty file
        if filepath.stat().st_size == 0:
            raise LoaderException(f"File is empty: {filepath}")
