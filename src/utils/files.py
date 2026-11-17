"""File integrity checks shared by ingestion and benchmarks."""
import hashlib
from pathlib import Path


def file_sha256(path):
    with Path(path).open('rb') as source:
        return hashlib.file_digest(source, 'sha256').hexdigest()
