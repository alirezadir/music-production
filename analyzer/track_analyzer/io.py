from __future__ import annotations

import json
from pathlib import Path


def safe_name(s: str) -> str:
    # filesystem-safe-ish, but readable
    return (
        s.strip()
        .replace("/", "-")
        .replace("\\", "-")
        .replace(":", " -")
        .replace("  ", " ")
    )


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_json(path: Path, obj: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


