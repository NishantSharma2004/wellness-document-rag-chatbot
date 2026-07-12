import hashlib
from pathlib import Path

def calculate_file_hash(filepath: Path) -> str:
    """Calculate the SHA-256 hash of a file."""
    sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        while True:
            data = f.read(65536)  # 64kb chunks
            if not data:
                break
            sha256.update(data)
    return sha256.hexdigest()
