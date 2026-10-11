"""
Chord/progression analysis pillar.
"""

from .chord_analysis import ChordAnalyzer
from .chord_utils import (
    bars_to_range,
    detect_key_from_chords,
    get_chord_notes,
    get_smooth_voicing,
    normalize_key_input,
    parse_chord,
    time_to_bars,
)

__all__ = [
    "ChordAnalyzer",
    "time_to_bars",
    "bars_to_range",
    "parse_chord",
    "get_chord_notes",
    "get_smooth_voicing",
    "detect_key_from_chords",
    "normalize_key_input",
]

# Optional: MIDI generation utilities (requires `midiutil`)
try:
    from .csv_chord_processor import analyze_chord_types, create_midi_with_chords
except ModuleNotFoundError:  # pragma: no cover
    analyze_chord_types = None  # type: ignore[assignment]
    create_midi_with_chords = None  # type: ignore[assignment]
else:
    __all__ += ["create_midi_with_chords", "analyze_chord_types"]


