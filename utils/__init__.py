"""
Shared utilities module.

Common functions used across multiple modules.
"""

from pathlib import Path
from typing import Optional, List
import os

def ensure_dir(path: Path) -> Path:
    """Ensure a directory exists, creating it if necessary."""
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path

def find_files(directory: Path, extensions: List[str], recursive: bool = True) -> List[Path]:
    """Find files with given extensions in a directory."""
    directory = Path(directory)
    if not directory.exists():
        return []
    
    files = []
    if recursive:
        for ext in extensions:
            files.extend(directory.rglob(f"*{ext}"))
    else:
        for ext in extensions:
            files.extend(directory.glob(f"*{ext}"))
    
    return sorted(files)

def get_file_hash(file_path: Path) -> str:
    """Compute MD5 hash of a file."""
    import hashlib
    hasher = hashlib.md5()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hasher.update(chunk)
    return hasher.hexdigest()

__all__ = [
    'ensure_dir',
    'find_files',
    'get_file_hash',
]

