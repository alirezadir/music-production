"""
Compatibility wrapper.

Historically this repo used flat modules at `analyzer/chord_analysis.py`.
The canonical implementation now lives in `analyzer/progression/chord_analysis.py`.
"""

from .progression.chord_analysis import *  # noqa: F403


