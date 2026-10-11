"""
Instagram Trending Songs Scraper
================================
Scrapes Instagram Reels/posts for trending songs related to configurable
topics (e.g. Iran revolution, free_iran, etc.).

Strategy (in priority order):
    1. instaloader  – pull recent Reels from public hashtag feeds and
       extract the embedded audio-track metadata.
    2. Web fallback – search aggregator sites (tokboard, trendpop,
       tokchart) via requests + BeautifulSoup for trending Instagram
       audio related to the same keywords.

Results are de-duplicated, ranked by frequency, and exported to
CSV / JSON in the `out/` directory.

Usage:
    python -m scraper.ig-trending-songs.scrape_ig_songs          # all topics
    python -m scraper.ig-trending-songs.scrape_ig_songs --topic iran_revolution_2026
    python -m scraper.ig-trending-songs.scrape_ig_songs --hashtags iranrevolution free_iran
"""
from __future__ import annotations

import argparse
import csv
import json
import logging
import re
import time
from collections import Counter
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

import requests

from .config import (
    IG_PASSWORD,
    IG_USERNAME,
    MAX_POSTS_PER_HASHTAG,
    OUTPUT_DIR,
    REQUEST_DELAY_SECONDS,
    TOPICS,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------
@dataclass
class SongHit:
    """A single occurrence of a song found in a post/reel."""

    song_title: str
    artist: str
    hashtag_source: str
    post_url: str = ""
    post_date: str = ""
    source_method: str = ""  # "instaloader" | "web_search"

    @property
    def key(self) -> str:
        return f"{self.song_title.lower().strip()}||{self.artist.lower().strip()}"


@dataclass
class TrendingSong:
    """Aggregated trending song across all sources."""

    song_title: str
    artist: str
    count: int = 0
    hashtags_found_in: list[str] = field(default_factory=list)
    sample_urls: list[str] = field(default_factory=list)
    sources: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# 1. Instaloader strategy
# ---------------------------------------------------------------------------
def _get_instaloader_instance():
    """Return a configured instaloader.Instaloader, or None if unavailable."""
    try:
        import instaloader  # noqa: F811
    except ImportError:
        log.warning("instaloader not installed – skipping direct IG scrape.")
        return None

    loader = instaloader.Instaloader(
        download_pictures=False,
        download_videos=False,
        download_video_thumbnails=False,
        download_geotags=False,
        download_comments=False,
        save_metadata=False,
        compress_json=False,
        quiet=True,
    )

    if IG_USERNAME and IG_PASSWORD:
        try:
            loader.login(IG_USERNAME, IG_PASSWORD)
            log.info("Logged in to Instagram as %s", IG_USERNAME)
        except Exception as exc:
            log.warning("IG login failed (%s) – continuing anonymously.", exc)
    else:
        log.info(
            "No IG credentials set (IG_USERNAME / IG_PASSWORD). "
            "Scraping anonymously – expect limited results."
        )

    return loader


def scrape_hashtag_instaloader(
    hashtag: str,
    max_posts: int = MAX_POSTS_PER_HASHTAG,
    delay: float = REQUEST_DELAY_SECONDS,
) -> list[SongHit]:
    """Scrape recent Reels from *hashtag* and extract audio metadata."""
    loader = _get_instaloader_instance()
    if loader is None:
        return []

    import instaloader

    hits: list[SongHit] = []
    try:
        ht = instaloader.Hashtag.from_name(loader.context, hashtag)
        log.info("Fetching posts for #%s …", hashtag)
        count = 0
        for post in ht.get_posts():
            if count >= max_posts:
                break
            count += 1

            # Reels / videos carry a .video_url; music metadata lives in
            # the GraphQL sidecar under ``post._full_metadata_dict``.
            try:
                meta = post._full_metadata_dict or {}
            except Exception:
                meta = {}

            song_title, artist = _extract_audio_from_meta(meta)

            if song_title:
                hits.append(
                    SongHit(
                        song_title=song_title,
                        artist=artist,
                        hashtag_source=hashtag,
                        post_url=f"https://www.instagram.com/p/{post.shortcode}/",
                        post_date=post.date_utc.isoformat() if post.date_utc else "",
                        source_method="instaloader",
                    )
                )

            # Caption-based fallback: look for "🎵 Song – Artist" patterns
            if not song_title and post.caption:
                fallback = _extract_song_from_caption(post.caption)
                if fallback:
                    hits.append(
                        SongHit(
                            song_title=fallback[0],
                            artist=fallback[1],
                            hashtag_source=hashtag,
                            post_url=f"https://www.instagram.com/p/{post.shortcode}/",
                            post_date=post.date_utc.isoformat()
                            if post.date_utc
                            else "",
                            source_method="instaloader_caption",
                        )
                    )

            time.sleep(delay)

    except instaloader.exceptions.QueryReturnedNotFoundException:
        log.warning("Hashtag #%s not found on Instagram.", hashtag)
    except instaloader.exceptions.ConnectionException as exc:
        log.warning("Connection error for #%s: %s", hashtag, exc)
    except Exception as exc:
        log.error("Unexpected error scraping #%s: %s", hashtag, exc)

    log.info("  #%s → %d song hits via instaloader", hashtag, len(hits))
    return hits


def _extract_audio_from_meta(meta: dict) -> tuple[str, str]:
    """
    Pull song title + artist from the IG GraphQL metadata dict.

    Instagram stores Reel audio info under various nested keys; this
    function checks the most common locations.
    """
    # clips_music_attribution_info  (Reels)
    music = meta.get("clips_music_attribution_info") or {}
    if music:
        return music.get("song_name", ""), music.get("artist_name", "")

    # music_info → music_asset_info  (newer schema)
    music_info = meta.get("music_info") or {}
    asset = music_info.get("music_asset_info") or {}
    if asset:
        return asset.get("title", ""), asset.get("display_artist", "")

    # edge_media_to_clip → clips_metadata
    clip_edge = meta.get("edge_media_to_clip") or {}
    for edge in clip_edge.get("edges", []):
        node = edge.get("node", {})
        clip_meta = node.get("clips_music_attribution_info") or {}
        if clip_meta:
            return clip_meta.get("song_name", ""), clip_meta.get("artist_name", "")

    return "", ""


_SONG_CAPTION_RE = re.compile(
    r"(?:🎵|🎶|♫|🎤|song|track|music)[:\s]*[\"']?(.+?)[\"']?\s*[-–—by]\s*(.+?)(?:\n|$|#)",
    re.IGNORECASE,
)


def _extract_song_from_caption(caption: str) -> Optional[tuple[str, str]]:
    """Best-effort regex to pull 'Song – Artist' from a caption."""
    m = _SONG_CAPTION_RE.search(caption)
    if m:
        return m.group(1).strip(), m.group(2).strip()
    return None


# ---------------------------------------------------------------------------
# 2. Web-search fallback
# ---------------------------------------------------------------------------
_WEB_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
}


def scrape_web_trending(
    keywords: list[str],
    delay: float = REQUEST_DELAY_SECONDS,
) -> list[SongHit]:
    """
    Search aggregator / news sites for trending Instagram songs related to
    the given *keywords*.

    Sites queried:
        - tokboard.com  (trending IG Reels audio)
        - Google search  "instagram trending songs {keyword} 2026"
    """
    hits: list[SongHit] = []

    for kw in keywords:
        hits.extend(_search_google_for_ig_songs(kw, delay=delay))
        time.sleep(delay)

    log.info("Web search returned %d total song hits.", len(hits))
    return hits


def _search_google_for_ig_songs(
    keyword: str,
    delay: float = 1.5,
) -> list[SongHit]:
    """
    Use a simple Google search to find articles listing trending
    Instagram songs for *keyword*.  Parse the titles for song names.
    """
    hits: list[SongHit] = []
    queries = [
        f"instagram reels trending songs {keyword} 2026",
        f"instagram trending audio {keyword}",
        f"viral instagram songs {keyword} revolution",
    ]

    for q in queries:
        try:
            url = "https://www.google.com/search"
            params = {"q": q, "num": 10, "hl": "en"}
            resp = requests.get(
                url, params=params, headers=_WEB_HEADERS, timeout=15
            )
            if resp.status_code != 200:
                continue

            songs = _parse_song_mentions_from_html(resp.text, keyword)
            hits.extend(songs)
        except Exception as exc:
            log.warning("Google search failed for '%s': %s", q, exc)

        time.sleep(delay)

    return hits


_SONG_HTML_RE = re.compile(
    r"["\"']([^"\"']{2,60})["\"']\s*(?:by|[-–—])\s*([A-Za-z0-9\s&,.]+)",
)


def _parse_song_mentions_from_html(
    html: str, keyword: str
) -> list[SongHit]:
    """Extract song-artist pairs from Google result snippets."""
    hits: list[SongHit] = []
    for m in _SONG_HTML_RE.finditer(html):
        title = m.group(1).strip()
        artist = m.group(2).strip()
        if len(title) < 2 or len(artist) < 2:
            continue
        # Skip obvious non-songs
        skip_words = {"search", "google", "instagram", "facebook", "http", "www"}
        if any(w in title.lower() for w in skip_words):
            continue
        hits.append(
            SongHit(
                song_title=title,
                artist=artist,
                hashtag_source=keyword,
                source_method="web_search",
            )
        )
    return hits


def scrape_tokboard(delay: float = REQUEST_DELAY_SECONDS) -> list[SongHit]:
    """
    Scrape tokboard.com for currently trending Instagram Reel audio.
    Returns whatever is on their front page – not keyword-specific.
    """
    hits: list[SongHit] = []
    try:
        resp = requests.get(
            "https://tokboard.com/instagram/trending-audio",
            headers=_WEB_HEADERS,
            timeout=15,
        )
        if resp.status_code != 200:
            log.warning("tokboard returned %d", resp.status_code)
            return hits

        from bs4 import BeautifulSoup

        soup = BeautifulSoup(resp.text, "html.parser")

        for card in soup.select(".audio-card, .track-card, tr, .song-item, li"):
            text = card.get_text(" ", strip=True)
            parts = re.split(r"\s*[-–—by]\s*", text, maxsplit=1)
            if len(parts) == 2 and 2 < len(parts[0]) < 80:
                hits.append(
                    SongHit(
                        song_title=parts[0].strip(),
                        artist=parts[1].strip()[:80],
                        hashtag_source="tokboard_trending",
                        source_method="tokboard",
                    )
                )
    except ImportError:
        log.warning("beautifulsoup4 not installed – skipping tokboard.")
    except Exception as exc:
        log.warning("tokboard scrape failed: %s", exc)

    log.info("tokboard → %d audio hits", len(hits))
    return hits


# ---------------------------------------------------------------------------
# Aggregation & ranking
# ---------------------------------------------------------------------------
def aggregate(hits: list[SongHit]) -> list[TrendingSong]:
    """De-duplicate and rank songs by frequency."""
    buckets: dict[str, list[SongHit]] = {}
    for h in hits:
        buckets.setdefault(h.key, []).append(h)

    songs: list[TrendingSong] = []
    for key, group in buckets.items():
        representative = group[0]
        hashtags = sorted({h.hashtag_source for h in group})
        urls = sorted({h.post_url for h in group if h.post_url})[:5]
        sources = sorted({h.source_method for h in group})
        songs.append(
            TrendingSong(
                song_title=representative.song_title,
                artist=representative.artist,
                count=len(group),
                hashtags_found_in=hashtags,
                sample_urls=urls,
                sources=sources,
            )
        )

    songs.sort(key=lambda s: s.count, reverse=True)
    return songs


# ---------------------------------------------------------------------------
# Export helpers
# ---------------------------------------------------------------------------
def export_json(songs: list[TrendingSong], path: Path) -> None:
    data = [asdict(s) for s in songs]
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False))
    log.info("Wrote %d songs to %s", len(songs), path)


def export_csv(songs: list[TrendingSong], path: Path) -> None:
    fieldnames = [
        "rank",
        "song_title",
        "artist",
        "count",
        "hashtags_found_in",
        "sample_urls",
        "sources",
    ]
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for i, s in enumerate(songs, 1):
            writer.writerow(
                {
                    "rank": i,
                    "song_title": s.song_title,
                    "artist": s.artist,
                    "count": s.count,
                    "hashtags_found_in": "; ".join(s.hashtags_found_in),
                    "sample_urls": "; ".join(s.sample_urls),
                    "sources": "; ".join(s.sources),
                }
            )
    log.info("Wrote %d songs to %s", len(songs), path)


def print_report(songs: list[TrendingSong], top_n: int = 30) -> None:
    print("\n" + "=" * 70)
    print(f"  TOP {min(top_n, len(songs))} TRENDING INSTAGRAM SONGS")
    print("=" * 70)
    for i, s in enumerate(songs[:top_n], 1):
        print(
            f"  {i:>3}.  {s.song_title}  –  {s.artist}  "
            f"(×{s.count}, hashtags: {', '.join(s.hashtags_found_in[:3])})"
        )
    print("=" * 70 + "\n")


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------
def run(
    hashtags: list[str] | None = None,
    topic: str | None = None,
    max_posts: int = MAX_POSTS_PER_HASHTAG,
    skip_instaloader: bool = False,
    skip_web: bool = False,
) -> list[TrendingSong]:
    """
    Run the full scraping pipeline.

    Args:
        hashtags: Explicit list of hashtags to scrape.
        topic: Topic name from config.TOPICS.
        max_posts: Max posts to fetch per hashtag via instaloader.
        skip_instaloader: Skip the instaloader strategy.
        skip_web: Skip the web-search fallback.

    Returns:
        Ranked list of TrendingSong.
    """
    if hashtags is None and topic is None:
        # Scrape all configured topics
        hashtags = []
        for tag_list in TOPICS.values():
            hashtags.extend(tag_list)
        hashtags = sorted(set(hashtags))
    elif topic:
        if topic not in TOPICS:
            log.error(
                "Unknown topic '%s'. Available: %s",
                topic,
                ", ".join(TOPICS.keys()),
            )
            return []
        hashtags = TOPICS[topic]

    log.info("Scraping %d hashtag(s): %s", len(hashtags), ", ".join(hashtags[:10]))

    all_hits: list[SongHit] = []

    # --- Strategy 1: instaloader -----------------------------------------
    if not skip_instaloader:
        for tag in hashtags:
            hits = scrape_hashtag_instaloader(tag, max_posts=max_posts)
            all_hits.extend(hits)

    # --- Strategy 2: web search ------------------------------------------
    if not skip_web:
        keyword_groups = [hashtags[i : i + 3] for i in range(0, len(hashtags), 3)]
        for group in keyword_groups:
            all_hits.extend(scrape_web_trending(group))

        all_hits.extend(scrape_tokboard())

    log.info("Total raw hits: %d", len(all_hits))

    songs = aggregate(all_hits)
    log.info("Unique songs after de-dup: %d", len(songs))

    # Export
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    label = topic or "all_topics"
    export_json(songs, OUTPUT_DIR / f"trending_songs_{label}_{ts}.json")
    export_csv(songs, OUTPUT_DIR / f"trending_songs_{label}_{ts}.csv")

    print_report(songs)
    return songs


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser(
        description="Scrape Instagram for trending songs by topic / hashtag.",
    )
    parser.add_argument(
        "--topic",
        type=str,
        default=None,
        help=f"Topic name from config. Choices: {', '.join(TOPICS.keys())}",
    )
    parser.add_argument(
        "--hashtags",
        nargs="+",
        default=None,
        help="Explicit hashtags to scrape (overrides --topic).",
    )
    parser.add_argument(
        "--max-posts",
        type=int,
        default=MAX_POSTS_PER_HASHTAG,
        help="Max posts per hashtag via instaloader (default: %(default)s).",
    )
    parser.add_argument(
        "--skip-instaloader",
        action="store_true",
        help="Skip instaloader (e.g. if not logged in).",
    )
    parser.add_argument(
        "--skip-web",
        action="store_true",
        help="Skip web-search fallback.",
    )
    args = parser.parse_args()

    run(
        hashtags=args.hashtags,
        topic=args.topic,
        max_posts=args.max_posts,
        skip_instaloader=args.skip_instaloader,
        skip_web=args.skip_web,
    )


if __name__ == "__main__":
    main()
