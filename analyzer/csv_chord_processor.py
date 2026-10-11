"""
Compatibility wrapper.

Historically this repo used flat modules at `analyzer/csv_chord_processor.py`.
The canonical implementation now lives in `analyzer/progression/csv_chord_processor.py`.
"""

from .progression.csv_chord_processor import *  # noqa: F403


