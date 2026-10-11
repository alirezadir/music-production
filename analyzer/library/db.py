from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, Optional


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class LibraryPaths:
    """
    Conventional paths for the track library layer.

    These are defaults; callers can override by CLI flags.
    """

    root_dir: Path

    @property
    def db_path(self) -> Path:
        return self.root_dir / "library.sqlite"

    @property
    def artifacts_dir(self) -> Path:
        return self.root_dir / "artifacts"


SCHEMA_SQL = """
PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS tracks (
  id TEXT PRIMARY KEY,
  source_path TEXT NOT NULL,
  sha256 TEXT,
  title TEXT,
  artist TEXT,
  label TEXT,
  bpm REAL,
  key TEXT,
  added_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_tracks_label ON tracks(label);
CREATE INDEX IF NOT EXISTS idx_tracks_artist ON tracks(artist);
CREATE INDEX IF NOT EXISTS idx_tracks_sha256 ON tracks(sha256);

CREATE TABLE IF NOT EXISTS tags (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS track_tags (
  track_id TEXT NOT NULL,
  tag_id INTEGER NOT NULL,
  added_at TEXT NOT NULL,
  PRIMARY KEY (track_id, tag_id),
  FOREIGN KEY (track_id) REFERENCES tracks(id) ON DELETE CASCADE,
  FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS analyses (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  track_id TEXT NOT NULL,
  analysis_type TEXT NOT NULL, -- e.g. 'mht', 'ableton', 'manual', 'llm'
  schema_version TEXT NOT NULL DEFAULT 'v1',
  created_at TEXT NOT NULL,
  payload_json TEXT NOT NULL,
  FOREIGN KEY (track_id) REFERENCES tracks(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_analyses_track_id ON analyses(track_id);
CREATE INDEX IF NOT EXISTS idx_analyses_type ON analyses(analysis_type);
"""


def connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON;")
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA_SQL)
    conn.commit()


def upsert_track(
    conn: sqlite3.Connection,
    *,
    track_id: str,
    source_path: str,
    sha256: Optional[str] = None,
    title: Optional[str] = None,
    artist: Optional[str] = None,
    label: Optional[str] = None,
    bpm: Optional[float] = None,
    key: Optional[str] = None,
) -> None:
    now = utc_now_iso()
    conn.execute(
        """
        INSERT INTO tracks (id, source_path, sha256, title, artist, label, bpm, key, added_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
          source_path=excluded.source_path,
          sha256=COALESCE(excluded.sha256, tracks.sha256),
          title=COALESCE(excluded.title, tracks.title),
          artist=COALESCE(excluded.artist, tracks.artist),
          label=COALESCE(excluded.label, tracks.label),
          bpm=COALESCE(excluded.bpm, tracks.bpm),
          key=COALESCE(excluded.key, tracks.key),
          updated_at=excluded.updated_at
        """,
        (track_id, source_path, sha256, title, artist, label, bpm, key, now, now),
    )
    conn.commit()


def ensure_tag(conn: sqlite3.Connection, name: str) -> int:
    name = name.strip()
    if not name:
        raise ValueError("Tag name is empty")
    conn.execute("INSERT OR IGNORE INTO tags (name) VALUES (?)", (name,))
    row = conn.execute("SELECT id FROM tags WHERE name=?", (name,)).fetchone()
    assert row is not None
    return int(row["id"])


def add_tags(conn: sqlite3.Connection, track_id: str, tags: Iterable[str]) -> None:
    now = utc_now_iso()
    for t in tags:
        tag_id = ensure_tag(conn, t)
        conn.execute(
            "INSERT OR IGNORE INTO track_tags (track_id, tag_id, added_at) VALUES (?, ?, ?)",
            (track_id, tag_id, now),
        )
    conn.commit()


def add_analysis(
    conn: sqlite3.Connection,
    *,
    track_id: str,
    analysis_type: str,
    payload: Dict[str, Any],
    schema_version: str = "v1",
) -> None:
    conn.execute(
        """
        INSERT INTO analyses (track_id, analysis_type, schema_version, created_at, payload_json)
        VALUES (?, ?, ?, ?, ?)
        """,
        (track_id, analysis_type, schema_version, utc_now_iso(), json.dumps(payload, ensure_ascii=False)),
    )
    conn.commit()


