"""Sidecar JSON metadata for generated MIDI files.

Reconstructed from the schema of existing outputs in out/midi-pack/*.json
(version 1.1.0): writes <midi stem>.json next to the MIDI file.
"""
import json
import os
import subprocess
from datetime import datetime, timezone

SCHEMA_VERSION = "1.1.0"
APP_NAME = "diream-ai"


def _git_commit() -> str | None:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=os.path.dirname(os.path.abspath(__file__)),
            capture_output=True, text=True, timeout=5,
        )
        return out.stdout.strip() or None
    except Exception:
        return None


def create_midi_metadata(script_name, midi_filepath, params=None, theory=None,
                         voicing=None, timeline=None, tags=None, derived=None):
    """Write metadata JSON beside midi_filepath and return its path."""
    now = datetime.now(timezone.utc)
    stem = os.path.splitext(os.path.basename(script_name))[0]
    if stem.startswith("make_"):
        stem = stem[len("make_"):]

    data = {
        "id": f"{stem}_{now.strftime('%Y%m%d_%H%M%S')}",
        "version": SCHEMA_VERSION,
        "created_at": now.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
        "generator": {
            "app": APP_NAME,
            "script": script_name,
            "commit": _git_commit(),
            "params": params or {},
        },
        "theory": theory or {},
    }
    if voicing is not None:
        data["voicing"] = voicing
    data["timeline"] = timeline or {}
    data["tags"] = list(tags or [])
    data["derived"] = derived or {}

    json_path = os.path.splitext(midi_filepath)[0] + ".json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    return json_path
