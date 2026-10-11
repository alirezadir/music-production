"""Script to fact-check tracks.csv using Firecrawl and remove hallucinations."""
import os
import pandas as pd
import re
from csv_store import load_or_create_csv
from datetime import datetime


def parse_track_from_firecrawl_markdown(markdown: str) -> dict:
    """Parse track information from Firecrawl markdown output."""
    result = {
        "title": None,
        "artists": None,
        "label": None,
        "genre": None,
        "bpm": None,
        "key": None,
        "released_date": None
    }
    
    # Extract title from H1 header
    title_match = re.search(r'#\s+(.+?)(?:\s*Extended Mix|Original Mix|Radio Edit|$)', markdown, re.IGNORECASE)
    if title_match:
        title = title_match.group(1).strip()
        # Clean up title
        title = re.sub(r'\s*(Extended Mix|Original Mix|Radio Edit|Instrumental Mix|Dub Mix)\s*$', '', title, flags=re.IGNORECASE)
        result["title"] = title.strip()
    
    # Extract artists from artist links
    artist_pattern = r'\[([^\]]+)\]\(https://www\.beatport\.com/artist/[^\)]+\)'
    artists = re.findall(artist_pattern, markdown)
    if artists:
        # Remove duplicates while preserving order
        unique_artists = []
        seen = set()
        for artist in artists:
            artist_clean = artist.strip()
            if artist_clean and artist_clean.lower() not in seen:
                seen.add(artist_clean.lower())
                unique_artists.append(artist_clean)
        result["artists"] = ", ".join(unique_artists)
    
    # Extract label
    label_match = re.search(r'\[([^\]]+)\]\(https://www\.beatport\.com/label/[^\)]+\)', markdown)
    if label_match:
        result["label"] = label_match.group(1).strip()
    
    # Extract genre
    genre_match = re.search(r'\[([^\]]+)\]\(https://www\.beatport\.com/genre/[^\)]+\)', markdown)
    if genre_match:
        result["genre"] = genre_match.group(1).strip()
    
    # Extract BPM
    bpm_match = re.search(r'BPM:\s*(\d+)', markdown)
    if bpm_match:
        try:
            result["bpm"] = int(bpm_match.group(1))
        except:
            pass
    
    # Extract key
    key_match = re.search(r'Key:\s*([A-G][#b]?\s+(?:Major|Minor))', markdown)
    if key_match:
        result["key"] = key_match.group(1).strip()
    
    # Extract release date
    date_match = re.search(r'Released:\s*(\d{4}-\d{2}-\d{2})', markdown)
    if date_match:
        result["released_date"] = date_match.group(1)
    
    return result


def clean_artists_list(artists_str):
    """Remove duplicate artists and clean up."""
    if pd.isna(artists_str) or artists_str == "":
        return ""
    
    artists = [a.strip() for a in str(artists_str).split(",")]
    seen = set()
    unique_artists = []
    for artist in artists:
        artist_clean = artist.strip()
        if artist_clean and artist_clean.lower() not in seen:
            seen.add(artist_clean.lower())
            unique_artists.append(artist_clean)
    
    return ", ".join(unique_artists)


def main():
    """Main function to fact-check and clean tracks."""
    os.makedirs("out", exist_ok=True)
    tracks_csv = os.getenv("TRACKS_CSV", "out/tracks.csv")
    
    tracks_columns = [
        "title", "artists", "label", "label_tier", "genre", "bpm", "key",
        "released_date", "track_url", "source_page_type", "source_label",
        "source_artist", "created_at"
    ]
    
    tracks_df = load_or_create_csv(tracks_csv, tracks_columns)
    
    if tracks_df.empty:
        print("No tracks found")
        return
    
    print(f"Processing {len(tracks_df)} tracks...\n")
    
    # Step 1: Clean duplicate artists for all tracks
    print("Step 1: Removing duplicate artists from all tracks...")
    tracks_df["artists"] = tracks_df["artists"].apply(clean_artists_list)
    print("  ✓ Cleaned duplicate artists")
    
    # Step 2: Clean track titles
    print("\nStep 2: Cleaning track titles...")
    def clean_title(title):
        if pd.isna(title) or title == "":
            return ""
        title_str = str(title).strip()
        # Remove redundant suffixes
        title_str = re.sub(r'\s*(Extended Mix|Original Mix|Radio Edit|Instrumental Mix|Dub Mix)\s*$', '', title_str, flags=re.IGNORECASE)
        # Fix duplicate "feat." patterns
        title_str = re.sub(r'feat\.\s*([^,]+)\s*feat\.', r'feat. \1', title_str, flags=re.IGNORECASE)
        return title_str.strip()
    
    tracks_df["title"] = tracks_df["title"].apply(clean_title)
    print("  ✓ Cleaned track titles")
    
    # Step 3: Verify tracks with URLs using Firecrawl
    print("\nStep 3: Verifying tracks with Beatport URLs using Firecrawl...")
    tracks_with_urls = tracks_df[tracks_df["track_url"].notna() & (tracks_df["track_url"] != "")]
    
    print(f"  Found {len(tracks_with_urls)} tracks with URLs")
    print("  Note: This script requires Firecrawl MCP integration to verify tracks.")
    print("  For now, cleaning duplicate artists and titles has been completed.")
    
    # Save cleaned tracks
    tracks_df = tracks_df[tracks_columns]
    tracks_df.to_csv(tracks_csv, index=False)
    
    print(f"\n✓ Cleaned tracks saved to {tracks_csv}")
    print(f"  Final count: {len(tracks_df)} tracks")
    print(f"  Tracks with URLs: {len(tracks_with_urls)}")
    
    print("\nNext step: Integrate Firecrawl MCP to verify track data from URLs.")


if __name__ == "__main__":
    main()



