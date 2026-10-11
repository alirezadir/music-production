from __future__ import annotations

import argparse
from pathlib import Path

from analyzer.library import db as libdb
from analyzer.library.ingest import ingest_one, iter_audio_files, normalize_tags
from analyzer.library.summarize import print_json, summarize_by_label


def cmd_init_db(args: argparse.Namespace) -> int:
    paths = libdb.LibraryPaths(root_dir=Path(args.library_dir))
    conn = libdb.connect(paths.db_path)
    libdb.init_db(conn)
    paths.artifacts_dir.mkdir(parents=True, exist_ok=True)
    print(f"Initialized DB: {paths.db_path}")
    print(f"Artifacts dir:  {paths.artifacts_dir}")
    return 0


def cmd_ingest(args: argparse.Namespace) -> int:
    paths = libdb.LibraryPaths(root_dir=Path(args.library_dir))
    conn = libdb.connect(paths.db_path)
    libdb.init_db(conn)

    music_dir = Path(args.music_dir)
    if not music_dir.exists():
        raise SystemExit(f"music_dir not found: {music_dir}")

    tags = normalize_tags(args.tags or [])

    n = 0
    for p in iter_audio_files(music_dir):
        res = ingest_one(p, compute_hash=not args.no_hash)
        libdb.upsert_track(
            conn,
            track_id=res.track_id,
            source_path=str(res.source_path),
            sha256=res.sha256,
            title=res.title,
            artist=res.artist,
            label=res.label,
        )
        if tags:
            libdb.add_tags(conn, res.track_id, tags)
        n += 1

    print(f"Ingested {n} audio files from {music_dir}")
    return 0


def cmd_add_tags(args: argparse.Namespace) -> int:
    paths = libdb.LibraryPaths(root_dir=Path(args.library_dir))
    conn = libdb.connect(paths.db_path)
    libdb.init_db(conn)

    tags = normalize_tags(args.tags or [])
    if not tags:
        raise SystemExit("No tags provided")

    libdb.add_tags(conn, args.track_id, tags)
    print(f"Added tags to {args.track_id}: {tags}")
    return 0


def cmd_summarize_labels(args: argparse.Namespace) -> int:
    paths = libdb.LibraryPaths(root_dir=Path(args.library_dir))
    conn = libdb.connect(paths.db_path)
    libdb.init_db(conn)
    groups = summarize_by_label(conn, limit=args.limit)
    print_json(groups)
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="tracklib", description="Track library (DB + ingest + summaries)")
    p.add_argument(
        "--library-dir",
        default=str(Path("library").absolute()),
        help="Root folder for the track library (contains library.sqlite + artifacts/)",
    )

    sub = p.add_subparsers(dest="cmd", required=True)

    p_init = sub.add_parser("init-db", help="Initialize the SQLite database")
    p_init.set_defaults(func=cmd_init_db)

    p_ingest = sub.add_parser("ingest", help="Ingest a folder of audio files into the DB")
    p_ingest.add_argument("--music-dir", required=True, help="Folder containing your favorite tracks (audio files)")
    p_ingest.add_argument("--no-hash", action="store_true", help="Skip SHA256 hashing (faster, less stable IDs)")
    p_ingest.add_argument(
        "--tags",
        nargs="*",
        default=[],
        help='Optional tags to attach to every ingested track (e.g. "afterlife" "melodic-techno")',
    )
    p_ingest.set_defaults(func=cmd_ingest)

    p_tags = sub.add_parser("add-tags", help="Add tags to a single track id")
    p_tags.add_argument("--track-id", required=True)
    p_tags.add_argument("--tags", nargs="*", required=True)
    p_tags.set_defaults(func=cmd_add_tags)

    p_sum = sub.add_parser("summarize-labels", help="Summarize common patterns by label")
    p_sum.add_argument("--limit", type=int, default=50)
    p_sum.set_defaults(func=cmd_summarize_labels)

    return p


def main() -> int:
    p = build_parser()
    args = p.parse_args()
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())


