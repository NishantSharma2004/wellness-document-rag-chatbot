import pytest
from pathlib import Path
import tempfile
from src.loaders.text_loader import TextLoader
from src.loaders.pdf_loader import PDFLoader
from src.loaders.docx_loader import DocxLoader
from src.loaders.pptx_loader import PptxLoader
from src.utils.exceptions import LoaderException

def test_text_loader():
    loader = TextLoader()
    with tempfile.NamedTemporaryFile(suffix=".txt", mode="w+", delete=False, encoding="utf-8") as f:
        f.write("Hello World Page 1\n\f\nHello World Page 2")
        temp_path = Path(f.name)
    
    try:
        pages = loader.load(temp_path)
        assert len(pages) >= 1
        assert "Hello World" in pages[0]["text"]
    finally:
        temp_path.unlink()

def test_loader_empty_file():
    loader = TextLoader()
    with tempfile.NamedTemporaryFile(suffix=".txt", mode="w+", delete=False) as f:
        temp_path = Path(f.name)
    
    try:
        with pytest.raises(LoaderException):
            loader.load(temp_path)
    finally:
        temp_path.unlink()

def test_loader_nonexistent_file():
    loader = TextLoader()
    with pytest.raises(LoaderException):
        loader.load(Path("nonexistent_file_path.txt"))
