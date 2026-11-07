#!/usr/bin/env python3
"""Generic local LALAL.AI API v1 stem-separation CLI."""

from __future__ import annotations

import argparse
import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path

from lalal_api import (
    EXTRACTION_LEVELS,
    MODELS,
    LalalError,
    delete_remote,
    download_track,
    resolve_outputs,
    select_track_pair,
    start_stem_task,
    upload_file,
    wait_for_tasks,
)


@dataclass(frozen=True)
class StemSpec:
    api_name: str
    isolated_label: str
    complement_label: str


STEMS = {
    "vocals": StemSpec("vocals", "vocals", "instrumental"),
    "drum": StemSpec("drum", "drums", "no_drums"),
    "bass": StemSpec("bass", "bass", "no_bass"),
    "piano": StemSpec("piano", "piano", "no_piano"),
    "guitar": StemSpec("guitar", "guitar", "no_guitar"),
    "electric_guitar": StemSpec(
        "electric_guitar", "electric_guitar", "no_electric_guitar"
    ),
    "acoustic_guitar": StemSpec(
        "acoustic_guitar", "acoustic_guitar", "no_acoustic_guitar"
    ),
    "synthesizer": StemSpec("synthesizer", "synth", "no_synth"),
    "strings": StemSpec("strings", "strings", "no_strings"),
    "wind": StemSpec("wind", "wind", "no_wind"),
}
ALIASES = {
    "vi": "vocals",
    "drums": "drum",
    "synth": "synthesizer",
    "eguitar": "electric_guitar",
    "aguitar": "acoustic_guitar",
}
ALL_STEMS = tuple(STEMS)
MODEL_COMPATIBILITY = {
    "andromeda": {"vocals", "drum", "piano", "bass", "guitar"},
    "perseus": {
        "vocals",
        "drum",
        "piano",
        "bass",
        "electric_guitar",
        "acoustic_guitar",
    },
    "orion": {
        "vocals",
        "drum",
        "piano",
        "bass",
        "electric_guitar",
        "acoustic_guitar",
    },
    "phoenix": {
        "vocals",
        "drum",
        "piano",
        "bass",
        "electric_guitar",
        "acoustic_guitar",
        "synthesizer",
        "strings",
        "wind",
    },
}


def normalize_request(value: str) -> str:
    return value.strip().lower().replace("-", "_").replace(" ", "_")


def expand_stems(requested: list[str]) -> list[str]:
    expanded: list[str] = []
    for raw in requested:
        value = normalize_request(raw)
        candidates = ALL_STEMS if value == "all" else (ALIASES.get(value, value),)
        for candidate in candidates:
            if candidate not in STEMS:
                choices = ", ".join((*STEMS, *ALIASES, "all"))
                raise LalalError(f"unknown stem '{raw}'; choose from: {choices}")
            if candidate not in expanded:
                expanded.append(candidate)
    return expanded


def validate_model(stems: list[str], splitter: str) -> None:
    if splitter == "auto":
        return
    compatible = MODEL_COMPATIBILITY[splitter]
    unsupported = [stem for stem in stems if stem not in compatible]
    if unsupported:
        names = ", ".join(unsupported)
        raise LalalError(
            f"splitter '{splitter}' does not support: {names}; use --splitter auto "
            "or choose compatible stems"
        )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="lalal-stems",
        description="Split one local audio file into one or more requested stems.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  lalal-stems song.wav vocals
  lalal-stems song.wav drums
  lalal-stems song.wav vi
  lalal-stems song.wav vocals drums bass
  lalal-stems song.wav all

The source is uploaded once per invocation. LALAL.AI charges processing time for
each requested split. Both the isolated and complementary track are downloaded.
""",
    )
    parser.add_argument("input", type=Path, help="input audio file")
    parser.add_argument("stems", nargs="+", help="stem names, aliases, or all")
    parser.add_argument("-o", "--output", type=Path, help="output directory")
    parser.add_argument("--splitter", choices=MODELS, default="auto")
    parser.add_argument(
        "--extraction-level", choices=EXTRACTION_LEVELS, default="deep_extraction"
    )
    parser.add_argument("--dereverb", action="store_true")
    parser.add_argument("--delete-remote", action="store_true")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--resume", action="store_true")
    mode.add_argument("--overwrite", action="store_true")
    parser.add_argument("--poll-interval", type=float, default=5.0)
    parser.add_argument("--timeout", type=int, default=60)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("-q", "--quiet", action="store_true")
    return parser


def _plan_outputs(
    output_dir: Path,
    source_name: str,
    stems: list[str],
    resume: bool,
    overwrite: bool,
) -> dict[str, dict[str, Path | None]]:
    plan = {}
    for stem in stems:
        spec = STEMS[stem]
        plan[stem] = resolve_outputs(
            output_dir,
            source_name,
            [spec.isolated_label, spec.complement_label],
            resume,
            overwrite,
        )
    return plan


def _print_plan(input_path: Path, output_dir: Path, stems: list[str]) -> None:
    print(f"Input: {input_path}")
    print(f"Output: {output_dir}")
    print(f"Requested splits ({len(stems)}):")
    for stem in stems:
        spec = STEMS[stem]
        print(
            f"  {stem}: {spec.isolated_label} + {spec.complement_label} "
            "(<API-returned-format>)"
        )
    print("Upload count: 1")
    print(f"Billable split count: {len(stems)}")


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    input_path = args.input.expanduser().resolve()
    if not input_path.is_file():
        print(f"ERROR: file not found: {input_path}", file=sys.stderr)
        return 1
    if args.poll_interval <= 0 or args.timeout <= 0:
        print("ERROR: timeout and poll interval must be greater than zero", file=sys.stderr)
        return 1
    try:
        stems = expand_stems(args.stems)
        validate_model(stems, args.splitter)
        source_name = input_path.stem
        output_dir = (
            args.output.expanduser().resolve()
            if args.output
            else input_path.parent / source_name
        )
        if args.dry_run:
            _print_plan(input_path, output_dir, stems)
            return 0

        plan = _plan_outputs(
            output_dir, source_name, stems, args.resume, args.overwrite
        )
        pending = [stem for stem in stems if not all(plan[stem].values())]
        if not pending:
            if not args.quiet:
                print("All requested outputs are already complete.")
            return 0

        key = os.getenv("LALAL_LICENSE")
        if not key:
            raise LalalError("set LALAL_LICENSE before running a paid split")

        if not args.quiet:
            print(f"Input: {input_path}")
            print(f"Output: {output_dir}")
            print(f"Requested splits ({len(pending)}): {', '.join(pending)}")
            print("Uploading source once...")

        source_id = None
        try:
            source_id = upload_file(input_path, key, args.timeout)
            tasks = {
                stem: start_stem_task(
                    source_id,
                    STEMS[stem].api_name,
                    key,
                    args.splitter,
                    args.extraction_level,
                    args.dereverb,
                    args.timeout,
                )
                for stem in pending
            }
            tracks_by_stem = wait_for_tasks(
                tasks,
                key,
                args.timeout,
                args.poll_interval,
                args.quiet,
                time.sleep,
            )
            completed: list[Path] = []
            for stem in pending:
                spec = STEMS[stem]
                isolated, complement = select_track_pair(
                    tracks_by_stem[stem], spec.api_name
                )
                for label, track in (
                    (spec.isolated_label, isolated),
                    (spec.complement_label, complement),
                ):
                    existing = plan[stem][label]
                    if existing:
                        completed.append(existing)
                        continue
                    completed.append(
                        download_track(
                            track,
                            output_dir,
                            source_name,
                            label,
                            args.timeout,
                            args.overwrite,
                        )
                    )
        finally:
            if args.delete_remote and source_id:
                try:
                    delete_remote(source_id, key, args.timeout)
                except Exception as exc:
                    print(f"WARNING: remote cleanup failed: {exc}", file=sys.stderr)

        if not args.quiet:
            print("Done:")
            for path in completed:
                print(f"  {path.name}")
        return 0
    except (LalalError, OSError, KeyError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
