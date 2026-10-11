from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Iterator, Optional, Tuple


AUDIO_EXTS = {".wav", ".aif", ".aiff", ".mp3", ".flac", ".m4a"}


@dataclass(frozen=True)
class IngestResult:
    track_id: str
    source_path: Path
    sha256: Optional[str]
    title: Optional[str]
    artist: Optional[str]
    label: Optional[str]


def iter_audio_files(root: Path) -> Iterator[Path]:
    for p in sorted(root.rglob("*")):
        if p.is_file() and p.suffix.lower() in AUDIO_EXTS:
            yield p


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            b = f.read(chunk_size)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def stable_track_id_from_sha(sha256: str) -> str:
    # Keep IDs short but stable; collision risk is negligible for this use-case.
    return f"t_{sha256[:16]}"


FILENAME_PATTERNS: Tuple[re.Pattern[str], ...] = (
    # "Artist - Title (Label)" (label optional)
    re.compile(r"^(?P<artist>.+?)\\s+-\\s+(?P<title>.+?)(?:\\s+\\((?P<label>.+)\\))?$"),
    # "Artist – Title (Label)" en dash
    re.compile(r"^(?P<artist>.+?)\\s+–\\s+(?P<title>.+?)(?:\\s+\\((?P<label>.+)\\))?$"),
)


def parse_filename_meta(stem: str) -> tuple[Optional[str], Optional[str], Optional[str]]:
    """
    Very light filename parsing.

    Returns: (title, artist, label)
    """
    s = stem.strip()
    for pat in FILENAME_PATTERNS:
        m = pat.match(s)
        if m:
            artist = (m.group("artist") or "").strip() or None
            title = (m.group("title") or "").strip() or None
            label = (m.groupdict().get("label") or "").strip() or None
            return title, artist, label
    return None, None, None


def ingest_one(path: Path, *, compute_hash: bool = True) -> IngestResult:
    sha = sha256_file(path) if compute_hash else None
    track_id = stable_track_id_from_sha(sha) if sha else f"t_path_{abs(hash(str(path)))}"
    title, artist, label = parse_filename_meta(path.stem)
    return IngestResult(
        track_id=track_id,
        source_path=path,
        sha256=sha,
        title=title,
        artist=artist,
        label=label,
    )


def normalize_tags(tags: Iterable[str]) -> list[str]:
    out: list[str] = []
    for t in tags:
        t = t.strip()
        if not t:
            continue
        out.append(t)
    # de-dupe in order
    seen = set()
    deduped = []
    for t in out:
        k = t.lower()
        if k in seen:
            continue
        seen.add(k)
        deduped.append(t)
    return deduped


