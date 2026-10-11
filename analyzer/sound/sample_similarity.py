"""
Lightweight similarity search for samples/sounds based on tokens.

This intentionally uses only the Python standard library so it works without
extra dependencies. Later, you can replace/augment this with learned embeddings
(e.g. CLAP, VGGish, OpenL3) + an ANN index (FAISS/HNSW).
"""

from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Tuple


def tokenize(text: str) -> List[str]:
    tokens = re.split(r"[-_\\s\\.\\(\\)\\[\\]/]+", (text or "").lower())
    return [t for t in tokens if t and not t.isdigit() and len(t) > 1]


def cosine_sim(a: Dict[str, float], b: Dict[str, float]) -> float:
    if not a or not b:
        return 0.0
    dot = 0.0
    for k, va in a.items():
        vb = b.get(k)
        if vb is not None:
            dot += va * vb
    na = math.sqrt(sum(v * v for v in a.values()))
    nb = math.sqrt(sum(v * v for v in b.values()))
    if na == 0.0 or nb == 0.0:
        return 0.0
    return dot / (na * nb)


def bow(tokens: Iterable[str]) -> Dict[str, float]:
    out: Dict[str, float] = {}
    for t in tokens:
        out[t] = out.get(t, 0.0) + 1.0
    return out


@dataclass(frozen=True)
class SimilarItem:
    id: str
    score: float
    meta: Dict[str, str]


class SampleSimilarityIndex:
    """
    A tiny in-memory index over sample names or tag strings.

    Expected input sources:
    - the JSON outputs produced by `sound/tag-sounds/analyze_samples_unified.py`
    - or a custom list of sample filenames
    """

    def __init__(self) -> None:
        self._items: List[Tuple[str, Dict[str, float], Dict[str, str]]] = []

    def add(self, item_id: str, text: str, meta: Dict[str, str] | None = None) -> None:
        vec = bow(tokenize(text))
        self._items.append((item_id, vec, dict(meta or {})))

    def query(self, text: str, k: int = 10) -> List[SimilarItem]:
        q = bow(tokenize(text))
        scored: List[SimilarItem] = []
        for item_id, vec, meta in self._items:
            scored.append(SimilarItem(id=item_id, score=cosine_sim(q, vec), meta=meta))
        scored.sort(key=lambda x: x.score, reverse=True)
        return scored[:k]

    @classmethod
    def from_tag_sounds_json(cls, path: Path) -> "SampleSimilarityIndex":
        """
        Supports JSON that contains:
        - `samples_by_folder`: {folder_name: [sample1.wav, ...]}
        """
        data = json.loads(Path(path).read_text())
        idx = cls()
        samples_by_folder = data.get("samples_by_folder", {}) or {}
        for folder, samples in samples_by_folder.items():
            for s in samples:
                idx.add(item_id=f"{folder}/{s}", text=f"{folder} {s}", meta={"folder": folder})
        return idx


