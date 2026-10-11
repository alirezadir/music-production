from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

Confidence = Literal["high", "medium", "low"]


@dataclass(frozen=True)
class AnalyzerInitSpec:
    artist: str
    title: str
    label_reference: str | None = None
    audio_path: str | None = None

    bpm: float | None = None
    time_signature: str = "4/4"

    key_center: str | None = None
    loop_bars: int | None = None


def default_analysis_json(spec: AnalyzerInitSpec) -> dict[str, Any]:
    """Minimal, machine-readable analysis object (matches docs/AI_TRACK_ANALYZER_PLAYBOOK.md)."""
    return {
        "track": {
            "title": spec.title,
            "artist": spec.artist,
            "label_reference": spec.label_reference or "",
            "audio_path": spec.audio_path or "",
        },
        "tempo": {
            "bpm": float(spec.bpm) if spec.bpm is not None else 0,
            "time_signature": spec.time_signature,
            "confidence": "low" if spec.bpm is None else "medium",
        },
        "sections": [],
        "layers": [],
        "progression": {
            "key_center": spec.key_center or "",
            "loop_bars": int(spec.loop_bars) if spec.loop_bars is not None else 0,
            "notes": "",
            "confidence": "low",
        },
        "automation_events": [],
        "vocals": {"has_vocals": None, "first_entry_bar": None, "notes": ""},
    }


