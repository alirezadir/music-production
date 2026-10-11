from __future__ import annotations

import re

from analyzer.arrangement_refiner.models import CookbookRuleHit, Section


def _is_probably_lyric_line(line: str) -> bool:
    """Heuristic: detect full lyric lines vs markers."""
    s = line.strip()
    if not s:
        return False
    if s.startswith(("+", "#", "-", "*")):
        return False
    if s.startswith("[") and "]" in s:
        return False
    # quoted lyric blocks count as lyric content too
    # but many of your drafts use quotes intentionally inside drops → that's what we want to flag.
    # Count words as a rough indicator.
    words = re.findall(r"[A-Za-z']+", s)
    return len(words) >= 4


def _section_kind(tags: tuple[str, ...]) -> str:
    joined = " ".join(t.upper() for t in tags)
    if "DROP" in joined:
        return "drop"
    if "BREAKDOWN" in joined or ("BREAK" in joined and "CHORUS" in joined):
        return "breakdown"
    if "CHORUS" in joined:
        return "chorus"
    if "VERSE" in joined:
        return "verse"
    if "INTRO" in joined:
        return "intro"
    if "OUTRO" in joined:
        return "outro"
    if "BUILD" in joined:
        return "build"
    return "other"


def check_crimson_rules(sections: list[Section]) -> list[CookbookRuleHit]:
    """Apply a small set of style rules derived from Crimson notes (melodic techno)."""
    hits: list[CookbookRuleHit] = []

    # Rule 1: Drops should not contain full vocal lines (allow chops/short fragments).
    for s in sections:
        kind = _section_kind(s.tags)
        if kind != "drop":
            continue
        lyric_lines = [ln for ln in s.lines if _is_probably_lyric_line(ln)]
        if lyric_lines:
            hits.append(
                CookbookRuleHit(
                    rule_id="crimson.vocals_in_drop",
                    severity="warn",
                    message="Drop section contains full lyric lines. For melodic techno, keep full vocals mainly in breakdown/chorus; drops are mostly instrumental (allow short chops/fragments).",
                    section_header=s.header,
                    example_lines=tuple(lyric_lines[:3]),
                )
            )

    # Rule 2: Encourage call/response separation if 'LEAD' appears in tags.
    for s in sections:
        if any("LEAD" in t.upper() for t in s.tags):
            hits.append(
                CookbookRuleHit(
                    rule_id="crimson.call_response",
                    severity="info",
                    message="Consider separating Lead into Call vs Response tracks (core structural pattern in Crimson notes).",
                    section_header=s.header,
                )
            )

    return hits


