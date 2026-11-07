#!/usr/bin/env python3
"""Four-stage local reconstruction workflow using LALAL.AI API v1."""

from __future__ import annotations

import argparse
import os
import sys
import time
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


def _run_stage(
    input_path: Path,
    stem: str,
    isolated_label: str | None,
    complement_label: str | None,
    args,
    key: str,
) -> dict[str, Path]:
    labels = [label for label in (isolated_label, complement_label) if label]
    existing = resolve_outputs(
        args.output_dir, args.source_name, labels, args.resume, args.overwrite
    )
    if all(existing.values()):
        if not args.quiet:
            print("      resume: existing outputs are complete")
        return {label: path for label, path in existing.items() if path}

    source_id = None
    try:
        if not args.quiet:
            missing = [label for label, path in existing.items() if path is None]
            print(f"      upload {input_path.name}; missing: {', '.join(missing)}")
        source_id = upload_file(input_path, key, args.timeout)
        task_id = start_stem_task(
            source_id,
            stem,
            key,
            args.splitter,
            args.extraction_level,
            args.dereverb,
            args.timeout,
        )
        tracks = wait_for_tasks(
            {stem: task_id},
            key,
            args.timeout,
            args.poll_interval,
            args.quiet,
            time.sleep,
        )[stem]
        isolated, complement = select_track_pair(tracks, stem)
        output_tracks = {
            isolated_label: isolated if isolated_label else None,
            complement_label: complement if complement_label else None,
        }
        completed: dict[str, Path] = {
            label: path for label, path in existing.items() if path
        }
        for label, track in output_tracks.items():
            if not label or track is None or completed.get(label):
                continue
            completed[label] = download_track(
                track,
                args.output_dir,
                args.source_name,
                label,
                args.timeout,
                args.overwrite,
            )
        return completed
    finally:
        if args.delete_remote and source_id:
            try:
                delete_remote(source_id, key, args.timeout)
            except Exception as exc:
                print(f"WARNING: remote cleanup failed: {exc}", file=sys.stderr)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="remake-stems",
        description="Build reconstruction stems with the established four-stage workflow.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Stages:
  1 input -> vocals + instrumental
  2 instrumental -> drums + instrumental_no_drums
  3 instrumental -> bass + instrumental_no_bass
  4 instrumental_no_drums -> secondary bass + instrumental_melodics

Examples:
  remake-stems "San-Francisco-HQ.wav"
  remake-stems song.wav --resume --delete-remote
  remake-stems song.wav --dry-run
""",
    )
    parser.add_argument("input", type=Path, help="input audio file")
    parser.add_argument("-o", "--output", type=Path, help="output directory")
    parser.add_argument("--license", dest="license_key", help="license override")
    parser.add_argument("--splitter", choices=MODELS, default="auto")
    parser.add_argument(
        "--extraction-level", choices=EXTRACTION_LEVELS, default="deep_extraction"
    )
    parser.add_argument("--dereverb", action="store_true")
    parser.add_argument("--delete-remote", action="store_true")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--overwrite", action="store_true")
    mode.add_argument("--resume", action="store_true")
    parser.add_argument("--keep-secondary-bass", action="store_true")
    parser.add_argument("--poll-interval", type=float, default=5.0)
    parser.add_argument("--timeout", type=int, default=60)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("-q", "--quiet", action="store_true")
    return parser


def _print_plan(input_path: Path, output_dir: Path, keep_secondary_bass: bool) -> None:
    print(f"Input: {input_path}")
    print(f"Output: {output_dir}")
    print("Stages:")
    print("  1. vocals + instrumental")
    print("  2. drums + instrumental_no_drums")
    print("  3. bass + instrumental_no_bass")
    suffix = " + bass_from_no_drums" if keep_secondary_bass else ""
    print(f"  4. instrumental_melodics{suffix}")
    print("Returned audio format is detected from downloaded file contents.")


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    input_path = args.input.expanduser().resolve()
    if not input_path.is_file():
        print(f"ERROR: file not found: {input_path}", file=sys.stderr)
        return 1
    if args.poll_interval <= 0 or args.timeout <= 0:
        print("ERROR: timeout and poll interval must be greater than zero", file=sys.stderr)
        return 1

    args.source_name = input_path.stem
    args.output_dir = (
        args.output.expanduser().resolve()
        if args.output
        else input_path.parent / args.source_name
    )
    if args.dry_run:
        _print_plan(input_path, args.output_dir, args.keep_secondary_bass)
        return 0

    key = args.license_key or os.getenv("LALAL_LICENSE")
    if not key:
        print("ERROR: set LALAL_LICENSE or pass --license", file=sys.stderr)
        return 1

    try:
        if not args.quiet:
            print(f"Remaking stems: {input_path}\nOutput: {args.output_dir}")

        if not args.quiet:
            print("\n[1/4] vocals + instrumental")
        stage1 = _run_stage(
            input_path, "vocals", "vocals", "instrumental", args, key
        )

        if not args.quiet:
            print("\n[2/4] drums from instrumental")
        stage2 = _run_stage(
            stage1["instrumental"],
            "drum",
            "drums",
            "instrumental_no_drums",
            args,
            key,
        )

        if not args.quiet:
            print("\n[3/4] bass from instrumental")
        stage3 = _run_stage(
            stage1["instrumental"],
            "bass",
            "bass",
            "instrumental_no_bass",
            args,
            key,
        )

        if not args.quiet:
            print("\n[4/4] melodics from instrumental_no_drums")
        stage4 = _run_stage(
            stage2["instrumental_no_drums"],
            "bass",
            "bass_from_no_drums" if args.keep_secondary_bass else None,
            "instrumental_melodics",
            args,
            key,
        )

        if not args.quiet:
            print("\nDone:")
            final_paths = {**stage1, **stage2, **stage3, **stage4}
            for label in (
                "vocals",
                "instrumental",
                "drums",
                "instrumental_no_drums",
                "bass",
                "instrumental_no_bass",
                "instrumental_melodics",
                "bass_from_no_drums",
            ):
                if label in final_paths:
                    print(f"  {final_paths[label].name}")
        return 0
    except (LalalError, OSError, KeyError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
