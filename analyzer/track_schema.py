"""
Shared output schema for the track analyzer.

This is the contract that all analysis pillars (chords / elements / patterns / arrangement)
should write into so downstream indexing + similarity search can be consistent.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


@dataclass
class TrackPillars:
    """
    Four pillars you described:
    1) chord_progressions
    2) elements (musical elements / instruments)
    3) patterns (sounds / motifs / audio patterns)
    4) arrangement
    """

    chord_progressions: Optional[Dict[str, Any]] = None
    elements: Optional[Dict[str, Any]] = None
    patterns: Optional[Dict[str, Any]] = None
    arrangement: Optional[Dict[str, Any]] = None


@dataclass
class TrackAnalysis:
    """
    Top-level analysis object; serialize with `to_dict()`.
    """

    track_id: str
    source_path: str
    analyzed_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    meta: Dict[str, Any] = field(default_factory=dict)
    pillars: TrackPillars = field(default_factory=TrackPillars)
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        # dataclasses.asdict() handles nested dataclasses too
        return asdict(self)


