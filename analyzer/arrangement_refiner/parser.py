from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from analyzer.arrangement_refiner.models import ReferenceSection, Section


_TAG_RE = re.compile(r"\[([^\]]+)\]")


def _is_section_header(line: str) -> bool:
    s = line.strip()
    if not s.startswith("["):
        return False
    return bool(_TAG_RE.findall(s))


def _parse_tags(line: str) -> tuple[str, ...]:
    return tuple(t.strip() for t in _TAG_RE.findall(line))


def parse_draft_sections_from_lines(lines: list[str]) -> list[Section]:
    """Parse draft arrangement sections from raw lines.

    Section header format: one line starting with [TAG][TAG]...
    Everything until the next section header is the section body (verbatim).
    """
    sections: list[Section] = []
    cur_header: str | None = None
    cur_tags: tuple[str, ...] = ()
    cur_body: list[str] = []

    def flush() -> None:
        nonlocal cur_header, cur_tags, cur_body
        if cur_header is None:
            return
        sections.append(Section(header=cur_header, tags=cur_tags, lines=tuple(cur_body)))
        cur_header = None
        cur_tags = ()
        cur_body = []

    for raw in lines:
        line = raw.rstrip("\n")
        if _is_section_header(line):
            flush()
            cur_header = line.strip()
            cur_tags = _parse_tags(line)
            cur_body = []
        else:
            if cur_header is None:
                # ignore preamble until first section marker
                continue
            cur_body.append(line)

    flush()
    return sections


def parse_draft_sections_from_md(path: Path) -> list[Section]:
    text = path.read_text(encoding="utf-8")
    return parse_draft_sections_from_lines(text.splitlines(True))


@dataclass(frozen=True)
class ReferenceParseResult:
    sections: list[ReferenceSection]
    source_excerpt: str


def parse_reference_from_comparison_md(path: Path) -> ReferenceParseResult:
    """Extract reference structure from the 'Proposed Structure (bar blocks)' list in the comparison doc.

    We look for numbered lines like:
    1. **INTRO (DJ-friendly)** — **2 × 8** (16 bars)
    """
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()

    # capture the relevant region if possible
    start_idx = None
    for i, ln in enumerate(lines):
        if ln.strip().lower().startswith("### proposed structure"):
            start_idx = i
            break

    region = lines[start_idx:] if start_idx is not None else lines

    out: list[ReferenceSection] = []
    excerpt_lines: list[str] = []

    line_re = re.compile(
        r"^\s*(\d+)\.\s+\*\*(?P<name>[^*]+)\*\*\s+—\s+\*\*(?P<blocks>\d+)\s*[×x]\s*8\*\*",
        re.IGNORECASE,
    )

    for ln in region:
        m = line_re.match(ln)
        if m:
            name = m.group("name").strip()
            blocks = int(m.group("blocks"))
            out.append(ReferenceSection(name=name, blocks_8=blocks))
            excerpt_lines.append(ln)

    if not out:
        # fallback: we at least provide an empty structure
        excerpt = ""
    else:
        excerpt = "\n".join(excerpt_lines).strip() + "\n"

    return ReferenceParseResult(sections=out, source_excerpt=excerpt)


