from __future__ import annotations

import argparse
from pathlib import Path

from analyzer.track_analyzer.io import safe_name, write_json, write_text
from analyzer.track_analyzer.schemas import AnalyzerInitSpec, default_analysis_json
from analyzer.track_analyzer.templates import (
    arrangement_template_md,
    layers_timeline_csv_header,
    skeleton_checklist_md,
    summary_md,
)


def _default_out_dir(out_root: Path, artist: str, title: str) -> Path:
    return out_root / safe_name(f"{artist} - {title}")


def cmd_init(args: argparse.Namespace) -> int:
    out_root = Path(args.out_root)
    out_dir = _default_out_dir(out_root, args.artist, args.title)

    spec = AnalyzerInitSpec(
        artist=args.artist,
        title=args.title,
        label_reference=args.label_reference,
        audio_path=args.audio_path,
        bpm=args.bpm,
        time_signature=args.time_signature,
        key_center=args.key_center,
        loop_bars=args.loop_bars,
    )

    # Folder layout (matches docs/AI_TRACK_ANALYZER_PLAYBOOK.md)
    d_inputs = out_dir / "01_inputs"
    d_notes = out_dir / "02_notes"
    d_json = out_dir / "03_json"
    d_timeline = out_dir / "04_timeline"
    d_templates = out_dir / "05_templates"
    d_midi = out_dir / "06_midi_drafts"

    for d in (d_inputs, d_notes, d_json, d_timeline, d_templates):
        d.mkdir(parents=True, exist_ok=True)

    # Write core artifacts
    write_text(d_notes / "summary.md", summary_md(spec))
    write_text(d_templates / "arrangement_template.md", arrangement_template_md(spec))
    write_text(d_templates / "skeleton_checklist.md", skeleton_checklist_md(spec))
    write_text(d_timeline / "layers_timeline.csv", layers_timeline_csv_header())
    write_json(d_json / "analysis.json", default_analysis_json(spec))

    # Optional MIDI drafts
    if args.make_midi_drafts:
        # Import lazily so the CLI works even if MIDI deps aren't installed.
        from analyzer.track_analyzer.midi_drafts import MidiDraftSpec, write_midi_drafts

        if spec.bpm is None or spec.loop_bars is None:
            raise SystemExit("--make-midi-drafts requires --bpm and --loop-bars (and optionally --key-center)")
        midi_spec = MidiDraftSpec(
            bpm=float(spec.bpm),
            time_signature=spec.time_signature,
            key_center=spec.key_center or "C minor",
            loop_bars=int(spec.loop_bars),
        )
        d_midi.mkdir(parents=True, exist_ok=True)
        written = write_midi_drafts(d_midi, midi_spec)
        write_json(d_json / "midi_drafts.json", {k: str(v) for k, v in written.items()})

    print(f"Initialized analysis pack: {out_dir}")
    print(f"- summary:     {d_notes / 'summary.md'}")
    print(f"- analysis:    {d_json / 'analysis.json'}")
    print(f"- timeline:    {d_timeline / 'layers_timeline.csv'}")
    print(f"- templates:   {d_templates}")
    if args.make_midi_drafts:
        print(f"- midi drafts: {d_midi}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="track-analyzer",
        description="Create analysis artifacts (JSON/CSV/MD) + optional MIDI draft placeholders",
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    p_init = sub.add_parser("init", help="Initialize an analysis output folder for a reference track")
    p_init.add_argument("--artist", required=True)
    p_init.add_argument("--title", required=True)
    p_init.add_argument("--label-reference", default=None)
    p_init.add_argument("--audio-path", default=None)
    p_init.add_argument("--out-root", default=str(Path("analysis_out").absolute()))

    p_init.add_argument("--bpm", type=float, default=None)
    p_init.add_argument("--time-signature", default="4/4")
    p_init.add_argument("--key-center", default=None, help='e.g. "F minor" or "C# minor"')
    p_init.add_argument("--loop-bars", type=int, default=None, help="e.g. 8 or 16")

    p_init.add_argument("--make-midi-drafts", action="store_true", help="Create chords/arp/bass draft MIDI clips")
    p_init.set_defaults(func=cmd_init)

    return p


def main() -> int:
    p = build_parser()
    args = p.parse_args()
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())


