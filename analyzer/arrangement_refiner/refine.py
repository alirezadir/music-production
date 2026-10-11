from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from analyzer.arrangement_refiner.cookbook_rules import check_crimson_rules
from analyzer.arrangement_refiner.models import CookbookRuleHit, ReferenceSection, Section
from analyzer.arrangement_refiner.parser import ReferenceParseResult, parse_reference_from_comparison_md


def _md_escape(s: str) -> str:
    return s.replace("\r\n", "\n").replace("\r", "\n")


def _sections_to_outline(sections: list[Section]) -> str:
    out = []
    for i, s in enumerate(sections, start=1):
        out.append(f"{i}. `{s.header}`  (lines: {len(s.lines)})")
    return "\n".join(out) + "\n"


def _reference_to_outline(ref: list[ReferenceSection]) -> str:
    if not ref:
        return "_No reference structure could be parsed._\n"
    out = []
    for i, r in enumerate(ref, start=1):
        blocks = f"{r.blocks_8}×8" if r.blocks_8 is not None else "?"
        out.append(f"{i}. **{r.name}** — {blocks}")
    return "\n".join(out) + "\n"


def _hits_to_md(hits: list[CookbookRuleHit]) -> str:
    if not hits:
        return "- No issues detected by the current rule set.\n"
    lines: list[str] = []
    for h in hits:
        hdr = f" ({h.section_header})" if h.section_header else ""
        lines.append(f"- **[{h.severity}] {h.rule_id}**{hdr}: {h.message}")
        if h.example_lines:
            lines.append("")
            lines.append("```")
            lines.extend(h.example_lines)
            lines.append("```")
    return "\n".join(lines).rstrip() + "\n"


def _verbatim_block(title: str, content: str) -> str:
    return f"### {title}\n\n```text\n{content.rstrip()}\n```\n"


def _render_original_verbatim(sections: list[Section]) -> str:
    parts: list[str] = []
    for s in sections:
        body = "\n".join([s.header, *s.lines]).rstrip() + "\n"
        parts.append(_verbatim_block(f"Original section: {s.header}", body))
    return "\n".join(parts).rstrip() + "\n"


def _render_refined_plan(
    draft_sections: list[Section],
    ref: list[ReferenceSection],
) -> str:
    """Create a cookbook-aligned plan WITHOUT deleting content.

    We don’t attempt a perfect rewrite. We output:
    - a target section order (from reference)
    - mapping hints to reuse existing draft blocks
    - specific guidance for any cookbook rule hits (e.g. vocals-in-drop)
    """
    # Simple mapping heuristic: try to find draft section whose tags include the reference keyword.
    def find_candidates(keyword: str) -> list[Section]:
        k = keyword.upper()
        cands = []
        for s in draft_sections:
            joined = " ".join(t.upper() for t in s.tags)
            if k in joined:
                cands.append(s)
        return cands

    lines: list[str] = []
    lines.append("## Refined Arrangement (Cookbook-aligned, no deletions)")
    lines.append("")
    lines.append("> This is a **re-organization + instruction layer**. The original draft is preserved verbatim below.")
    lines.append("")

    if not ref:
        lines.append("_No parsed reference structure. Provide a comparison/reference file that includes the 'Proposed Structure (bar blocks)' list._")
        lines.append("")
        return "\n".join(lines).rstrip() + "\n"

    for i, r in enumerate(ref, start=1):
        blocks = f"{r.blocks_8}×8" if r.blocks_8 is not None else "?"
        lines.append(f"### {i}. {r.name} ({blocks})")
        lines.append("")
        # hint: map to a draft section if exists
        k = r.name.split("(", 1)[0].strip().split()[0].upper()
        cands = find_candidates(k)
        if cands:
            lines.append("**Candidate draft blocks to reuse (verbatim):**")
            for s in cands[:4]:
                lines.append(f"- `{s.header}`")
        else:
            lines.append("**Candidate draft blocks to reuse:** _none detected_")
        lines.append("")
        lines.append("**Instruction (what should happen here):**")
        if "DROP" in r.name.upper():
            lines.append("- Keep drop **mostly instrumental** (stabs + call/response + groove + bass movement).")
            lines.append("- If any vocal is present, use **short chops/fragments**, not full lines.")
        if "BREAKDOWN" in r.name.upper() or "CHORUS" in r.name.upper():
            lines.append("- This is where the **vocal identity** can live (full lines + harmonies).")
        if "VERSE" in r.name.upper():
            lines.append("- Verse is typically the section **after first vocal entry** (instrumental continuation/variation).")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def build_llm_prompt(
    *,
    draft_paths: list[Path],
    reference_path: Path,
    cookbook_path: Path | None,
) -> str:
    """Create an LLM-ready prompt using local markdown files.

    This does NOT call an LLM. It produces a prompt you can paste into any agent.
    """
    draft_texts = []
    for p in draft_paths:
        draft_texts.append(f"## Draft input: `{p}`\n\n```text\n{p.read_text(encoding='utf-8').rstrip()}\n```\n")

    ref_text = reference_path.read_text(encoding="utf-8").rstrip()
    cookbook_text = cookbook_path.read_text(encoding="utf-8").rstrip() if cookbook_path else ""

    return (
        "You are an Arrangement Refiner for melodic techno.\n"
        "Task: take the draft arrangement(s) below and output an improved version aligned to the reference structure and the Crimson cookbook rules.\n\n"
        "Hard rules:\n"
        "- Do NOT delete any lyrical content; if you need to move something, move it and keep it verbatim.\n"
        "- Drops should be mostly instrumental; keep full vocals mainly in breakdown/chorus (allow short chops in drops).\n"
        "- Use 8-bar blocks; prefer 16/32-bar phrases.\n\n"
        "Output requirements:\n"
        "- Produce a single refined Markdown arrangement.\n"
        "- Include a short change log.\n"
        "- Keep the original draft content verbatim at the bottom for traceability.\n\n"
        + (f"## Cookbook (Crimson notes)\n\n```text\n{cookbook_text}\n```\n\n" if cookbook_text else "")
        + "## Reference arrangement\n\n```text\n"
        + ref_text
        + "\n```\n\n"
        + "\n".join(draft_texts)
    )


def refine_to_markdown(
    *,
    draft_path: Path,
    reference_path: Path,
    cookbook_path: Path | None = None,
) -> tuple[str, dict]:
    """Refine a draft arrangement into a cookbook-aligned output markdown.

    Returns (markdown, metadata_json_dict).
    """
    draft_sections = parse_draft_from_file(draft_path)
    ref_res: ReferenceParseResult = parse_reference_from_comparison_md(reference_path)
    hits = check_crimson_rules(draft_sections)

    md_parts: list[str] = []
    md_parts.append(f"# Refined Arrangement — {draft_path.name}")
    md_parts.append("")
    md_parts.append("**Inputs**")
    md_parts.append(f"- Draft: `{draft_path}`")
    md_parts.append(f"- Reference: `{reference_path}`")
    md_parts.append(f"- Cookbook: `{cookbook_path}`" if cookbook_path else "- Cookbook: (none provided)")
    md_parts.append("")
    md_parts.append("---")
    md_parts.append("")
    md_parts.append("## Draft outline (parsed)")
    md_parts.append("")
    md_parts.append(_sections_to_outline(draft_sections))
    md_parts.append("")
    md_parts.append("## Reference outline (parsed)")
    md_parts.append("")
    md_parts.append(_reference_to_outline(ref_res.sections))
    md_parts.append("")
    md_parts.append("## Cookbook checks (Crimson rules)")
    md_parts.append("")
    md_parts.append(_hits_to_md(hits))
    md_parts.append("")
    md_parts.append("---")
    md_parts.append("")
    md_parts.append(_render_refined_plan(draft_sections, ref_res.sections))
    md_parts.append("")
    md_parts.append("---")
    md_parts.append("")
    md_parts.append("## Original draft (verbatim, preserved)")
    md_parts.append("")
    md_parts.append(_render_original_verbatim(draft_sections))

    out_md = "\n".join(md_parts).rstrip() + "\n"

    meta = {
        "draft_path": str(draft_path),
        "reference_path": str(reference_path),
        "cookbook_path": str(cookbook_path) if cookbook_path else None,
        "draft_sections": [
            {"header": s.header, "tags": list(s.tags), "line_count": len(s.lines)} for s in draft_sections
        ],
        "reference_sections": [asdict(r) for r in ref_res.sections],
        "cookbook_hits": [asdict(h) for h in hits],
    }
    return out_md, meta


def parse_draft_from_file(path: Path) -> list[Section]:
    from analyzer.arrangement_refiner.parser import parse_draft_sections_from_md

    return parse_draft_sections_from_md(path)


def write_refinement_outputs(
    *,
    draft_path: Path,
    reference_path: Path,
    cookbook_path: Path | None,
    out_md_path: Path,
    out_json_path: Path,
    out_prompt_path: Path | None,
) -> None:
    out_md, meta = refine_to_markdown(
        draft_path=draft_path,
        reference_path=reference_path,
        cookbook_path=cookbook_path,
    )

    out_md_path.parent.mkdir(parents=True, exist_ok=True)
    out_md_path.write_text(out_md, encoding="utf-8")

    out_json_path.parent.mkdir(parents=True, exist_ok=True)
    out_json_path.write_text(json.dumps(meta, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    if out_prompt_path is not None:
        prompt = build_llm_prompt(
            draft_paths=[draft_path],
            reference_path=reference_path,
            cookbook_path=cookbook_path,
        )
        out_prompt_path.parent.mkdir(parents=True, exist_ok=True)
        out_prompt_path.write_text(_md_escape(prompt), encoding="utf-8")


