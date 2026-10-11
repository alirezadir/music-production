"""
Compatibility wrapper.

Historically this repo used flat modules at `analyzer/chord_utils.py`.
The canonical implementation now lives in `analyzer/progression/chord_utils.py`.
"""

from .progression.chord_utils import *  # noqa: F403


