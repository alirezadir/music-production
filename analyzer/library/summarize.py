from __future__ import annotations

import json
import sqlite3
from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class GroupSummary:
    group_key: str
    n_tracks: int
    top_tags: List[str]
    top_bpm_buckets: List[str]
    top_keys: List[str]


def _bpm_bucket(bpm: Optional[float]) -> Optional[str]:
    if bpm is None:
        return None
    try:
        b = float(bpm)
    except Exception:
        return None
    # 5-bpm buckets: 120–124, 125–129, etc.
    lo = int(b // 5) * 5
    hi = lo + 4
    return f"{lo}-{hi}"


def summarize_by_label(conn: sqlite3.Connection, *, limit: int = 50) -> List[GroupSummary]:
    labels = conn.execute(
        "SELECT label, COUNT(*) AS n FROM tracks WHERE label IS NOT NULL GROUP BY label ORDER BY n DESC LIMIT ?",
        (limit,),
    ).fetchall()
    out: List[GroupSummary] = []
    for row in labels:
        label = row["label"]
        track_rows = conn.execute(
            "SELECT id, bpm, key FROM tracks WHERE label=?",
            (label,),
        ).fetchall()

        track_ids = [r["id"] for r in track_rows]
        tag_rows = conn.execute(
            """
            SELECT tags.name AS name
            FROM track_tags
            JOIN tags ON tags.id = track_tags.tag_id
            WHERE track_tags.track_id IN ({})
            """.format(
                ",".join("?" for _ in track_ids) if track_ids else "NULL"
            ),
            tuple(track_ids),
        ).fetchall() if track_ids else []

        tag_counter = Counter([r["name"] for r in tag_rows])
        bpm_counter = Counter([b for b in (_bpm_bucket(r["bpm"]) for r in track_rows) if b])
        key_counter = Counter([k for k in (r["key"] for r in track_rows) if k])

        out.append(
            GroupSummary(
                group_key=str(label),
                n_tracks=len(track_rows),
                top_tags=[t for t, _ in tag_counter.most_common(10)],
                top_bpm_buckets=[b for b, _ in bpm_counter.most_common(10)],
                top_keys=[k for k, _ in key_counter.most_common(10)],
            )
        )
    return out


def to_jsonable(groups: List[GroupSummary]) -> List[Dict[str, Any]]:
    return [
        {
            "group_key": g.group_key,
            "n_tracks": g.n_tracks,
            "top_tags": g.top_tags,
            "top_bpm_buckets": g.top_bpm_buckets,
            "top_keys": g.top_keys,
        }
        for g in groups
    ]


def print_json(groups: List[GroupSummary]) -> None:
    print(json.dumps(to_jsonable(groups), indent=2, ensure_ascii=False))


