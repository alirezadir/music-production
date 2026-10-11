"""Data models for track metadata."""
from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass
class TrackMeta:
    """Metadata for a track."""
    title: str
    artists: str  # Comma-separated artist names
    label: str
    genre: str
    bpm: Optional[float] = None
    key: Optional[str] = None
    released_date: Optional[str] = None  # ISO date string
    track_url: str = ""
    source_page_type: str = ""  # "label_top10", "label_tracks", "artist_tracks"
    label_tier: str = "unknown"  # "A", "B", "unknown"
    source_label: Optional[str] = None
    source_artist: Optional[str] = None
    
    def to_dict(self) -> dict:
        """Convert to dictionary for DataFrame."""
        return {
            "title": self.title,
            "artists": self.artists,
            "label": self.label,
            "label_tier": self.label_tier,
            "genre": self.genre,
            "bpm": self.bpm,
            "key": self.key or "",
            "released_date": self.released_date or "",
            "track_url": self.track_url,
            "source_page_type": self.source_page_type,
            "source_label": self.source_label or "",
            "source_artist": self.source_artist or "",
            "created_at": datetime.now().isoformat()
        }

