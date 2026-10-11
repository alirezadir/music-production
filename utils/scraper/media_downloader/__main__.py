"""
CLI entry point for the media downloader.

Usage:
    python -m scraper.media_downloader                          # default: links.txt → downloads/
    python -m scraper.media_downloader -f my_links.txt -o ~/Music/downloads
    python -m scraper.media_downloader -f links.txt --headed     # watch the browser
    python -m scraper.media_downloader -f links.txt --retries 3
"""
from __future__ import annotations

import argparse
import asyncio
import logging
import sys
from pathlib import Path

from .downloader import run

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)


def main() -> None:
    project_root = Path(__file__).resolve().parent.parent.parent

    parser = argparse.ArgumentParser(
        description=(
            "Download YouTube / Instagram media as audio (MP3-320) or "
            "video (1080p+) via free converter sites."
        ),
    )
    parser.add_argument(
        "-f", "--file",
        type=Path,
        default=project_root / "data" / "tracks-ig.txt",
        help="Text file with URLs (default: data/tracks-ig.txt)",
    )
    parser.add_argument(
        "-o", "--output",
        type=Path,
        default=project_root / "data" / "downloads",
        help="Destination directory for downloaded files (default: data/downloads/)",
    )
    parser.add_argument(
        "--headed",
        action="store_true",
        help="Run with a visible browser window (useful for debugging).",
    )
    parser.add_argument(
        "--retries",
        type=int,
        default=2,
        help="Number of retry attempts per URL (default: 2).",
    )
    args = parser.parse_args()

    if not args.file.exists():
        print(f"Error: links file not found: {args.file}")
        print(f"Create it with one URL per line. See links.txt.example for format.")
        sys.exit(1)

    results = asyncio.run(
        run(
            links_file=args.file,
            dest_dir=args.output,
            headless=not args.headed,
            retries=args.retries,
        )
    )

    if any(v == "failed" for v in results.values()):
        sys.exit(1)


if __name__ == "__main__":
    main()
