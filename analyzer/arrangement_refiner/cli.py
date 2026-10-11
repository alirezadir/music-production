from __future__ import annotations

import argparse
from pathlib import Path

from analyzer.arrangement_refiner.refine import write_refinement_outputs


def cmd_refine(args: argparse.Namespace) -> int:
    draft = Path(args.draft)
    ref = Path(args.reference)
    cookbook = Path(args.cookbook) if args.cookbook else None

    if not draft.exists():
        raise SystemExit(f"Draft not found: {draft}")
    if not ref.exists():
        raise SystemExit(f"Reference not found: {ref}")
    if cookbook is not None and not cookbook.exists():
        raise SystemExit(f"Cookbook not found: {cookbook}")

    out_md = Path(args.out_md) if args.out_md else draft.with_name(draft.stem + "-REFINED.md")
    out_json = Path(args.out_json) if args.out_json else out_md.with_suffix(".json")
    out_prompt = Path(args.out_prompt) if args.out_prompt else (out_md.with_name(out_md.stem + "-PROMPT.txt") if args.emit_prompt else None)

    write_refinement_outputs(
        draft_path=draft,
        reference_path=ref,
        cookbook_path=cookbook,
        out_md_path=out_md,
        out_json_path=out_json,
        out_prompt_path=out_prompt,
    )

    print(f"Wrote refined Markdown: {out_md}")
    print(f"Wrote metadata JSON:   {out_json}")
    if out_prompt is not None:
        print(f"Wrote LLM prompt:      {out_prompt}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="arrangement-refiner",
        description="Refine a draft arrangement markdown using a reference structure and cookbook rules (human-in-the-loop).",
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    pr = sub.add_parser("refine", help="Refine a draft arrangement")
    pr.add_argument("--draft", required=True, help="Draft arrangement markdown (e.g. Everything-You-Do-Lyrics-IMPROVED-V2.md)")
    pr.add_argument("--reference", required=True, help="Reference arrangement markdown (e.g. comparison doc with Proposed Structure)")
    pr.add_argument("--cookbook", default=None, help="Cookbook markdown (e.g. crimson merged notes)")

    pr.add_argument("--out-md", default=None, help="Output refined markdown path")
    pr.add_argument("--out-json", default=None, help="Output metadata JSON path")
    pr.add_argument("--emit-prompt", action="store_true", help="Also write an LLM-ready prompt file")
    pr.add_argument("--out-prompt", default=None, help="Output prompt path (defaults next to output md)")

    pr.set_defaults(func=cmd_refine)
    return p


def main() -> int:
    p = build_parser()
    args = p.parse_args()
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())


