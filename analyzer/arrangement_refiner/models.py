from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

Confidence = Literal["high", "medium", "low"]


@dataclass(frozen=True)
class Section:
    header: str               # raw header line, e.g. "[DROP 1][VERSE][YOU TOUCH][M/F]"
    tags: tuple[str, ...]     # parsed tags in order, e.g. ("DROP 1", "VERSE", "YOU TOUCH", "M/F")
    lines: tuple[str, ...]    # section body lines (verbatim)


@dataclass(frozen=True)
class ReferenceSection:
    name: str                 # e.g. "INTRO (DJ-friendly)"
    blocks_8: int | None      # e.g. 2 means 2×8 bars
    notes: str = ""


@dataclass(frozen=True)
class CookbookRuleHit:
    rule_id: str
    severity: Literal["info", "warn", "error"]
    message: str
    section_header: str | None = None
    example_lines: tuple[str, ...] = ()


