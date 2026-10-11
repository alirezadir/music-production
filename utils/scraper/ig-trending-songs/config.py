"""
Configuration for Instagram trending-songs scraper.

Topics are lists of hashtags / search terms to monitor.
Each topic has a name and a list of related hashtags.
"""
import os
from pathlib import Path

OUTPUT_DIR = Path(__file__).parent / "out"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

IG_USERNAME = os.getenv("IG_USERNAME", "")
IG_PASSWORD = os.getenv("IG_PASSWORD", "")

MAX_POSTS_PER_HASHTAG = int(os.getenv("IG_MAX_POSTS", "50"))
REQUEST_DELAY_SECONDS = float(os.getenv("IG_REQUEST_DELAY", "2.0"))

TOPICS: dict[str, list[str]] = {
    "iran_revolution_2026": [
        "iranrevolution",
        "iranrevolution2026",
        "mahsa_amini",
        "free_iran",
        "freeiran",
        "womanlifefreedom",
        "zan_zendegi_azadi",
        "iranprotests",
        "iranprotests2026",
        "baraye",
    ],
    "iran_general": [
        "iran",
        "iranian",
        "persia",
        "persian",
        "iranmusic",
        "persianmusic",
        "tehran",
    ],
    "free_iran": [
        "free_iran",
        "freeiran",
        "freeiranians",
        "iranfreedom",
        "sayhernamemahsa",
    ],
}
