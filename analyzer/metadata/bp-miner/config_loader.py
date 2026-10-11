"""Configuration loader module."""
import json
import os
from typing import Dict, Any


def load_config(path: str = None) -> Dict[str, Any]:
    """
    Load configuration from JSON file.
    
    Args:
        path: Path to config file. If None, uses CONFIG_PATH env var or default.
    
    Returns:
        Configuration dictionary.
    """
    if path is None:
        path = os.getenv("CONFIG_PATH", "config.json")
    
    # Resolve relative paths from project root
    if not os.path.isabs(path):
        project_root = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(project_root, path)
    
    with open(path, "r", encoding="utf-8") as f:
        config = json.load(f)
    
    return config

