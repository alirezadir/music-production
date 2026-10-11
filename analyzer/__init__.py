"""
Music analysis module.

Provides tools for analyzing musical content including:
- Chord progressions
- Ableton Live projects
- Audio tracks (MHT pipeline)
"""

try:
    from .chord_analysis import ChordAnalyzer
    from .chord_utils import (
        time_to_bars,
        bars_to_range,
        parse_chord,
        get_chord_notes,
        get_smooth_voicing,
        detect_key_from_chords,
        normalize_key_input,
    )
except ModuleNotFoundError:  # pragma: no cover
    ChordAnalyzer = None  # type: ignore[assignment]
    time_to_bars = None  # type: ignore[assignment]
    bars_to_range = None  # type: ignore[assignment]
    parse_chord = None  # type: ignore[assignment]
    get_chord_notes = None  # type: ignore[assignment]
    get_smooth_voicing = None  # type: ignore[assignment]
    detect_key_from_chords = None  # type: ignore[assignment]
    normalize_key_input = None  # type: ignore[assignment]
from .ableton_analyzer import AbletonAnalyzer, AbletonProjectReader
from .track_schema import TrackAnalysis, TrackPillars

# Optional: MIDI generation utilities (requires `midiutil`)
try:
    from .csv_chord_processor import create_midi_with_chords, analyze_chord_types
except ModuleNotFoundError:  # pragma: no cover
    create_midi_with_chords = None  # type: ignore[assignment]
    analyze_chord_types = None  # type: ignore[assignment]

__all__ = ["AbletonAnalyzer", "AbletonProjectReader", "TrackAnalysis", "TrackPillars"]

if ChordAnalyzer is not None:
    __all__ += [
        "ChordAnalyzer",
        "time_to_bars",
        "bars_to_range",
        "parse_chord",
        "get_chord_notes",
        "get_smooth_voicing",
        "detect_key_from_chords",
        "normalize_key_input",
    ]

if create_midi_with_chords is not None and analyze_chord_types is not None:
    __all__ += ["create_midi_with_chords", "analyze_chord_types"]
