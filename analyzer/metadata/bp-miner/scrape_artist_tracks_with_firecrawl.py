"""Script to scrape artist tracks using Firecrawl MCP to discover B-level labels."""
import os
import sys
import pandas as pd
import re
from config_loader import load_config
from csv_store import load_or_create_csv, append_and_save
from models import TrackMeta
from datetime import datetime


def parse_tracks_from_firecrawl_markdown(markdown: str, artist_name: str) -> list:
    """Parse tracks from Firecrawl markdown output."""
    tracks = []
    
    # Pattern to match track entries in the markdown
    # Look for track URLs and extract metadata
    track_url_pattern = r'https://www\.beatport\.com/track/([^/\s]+)/(\d+)'
    
    # Split by track entries - look for track titles and labels
    lines = markdown.split('\n')
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # Look for track URLs
        url_match = re.search(track_url_pattern, line)
        if url_match:
            track_slug = url_match.group(1)
            track_id = url_match.group(2)
            track_url = f"https://www.beatport.com/track/{track_slug}/{track_id}"
            
            # Extract title from previous lines (often in brackets or bold)
            title = None
            label = None
            artists = artist_name
            genre = None
            bpm = None
            key = None
            released_date = None
            
            # Look backwards and forwards for metadata
            for j in range(max(0, i-5), min(len(lines), i+10)):
                check_line = lines[j]
                
                # Extract title (often in brackets or after "Play")
                if not title:
                    title_match = re.search(r'\[([^\]]+)\]\(https://www\.beatport\.com/track/', check_line)
                    if title_match:
                        title = title_match.group(1).strip()
                    elif 'Play' in check_line and j < i:
                        # Title might be in previous line
                        if j > 0:
                            prev_line = lines[j-1].strip()
                            if prev_line and not prev_line.startswith('['):
                                title = prev_line
                
                # Extract label (look for label links)
                if not label:
                    label_match = re.search(r'\[([^\]]+)\]\(https://www\.beatport\.com/label/', check_line)
                    if label_match:
                        label = label_match.group(1).strip()
                
                # Extract BPM and Key
                if not bpm:
                    bpm_match = re.search(r'(\d+)\s+BPM', check_line)
                    if bpm_match:
                        bpm = int(bpm_match.group(1))
                
                if not key:
                    key_match = re.search(r'[\\-]\s*([A-G][#b]?\s+(?:Major|Minor))', check_line)
                    if key_match:
                        key = key_match.group(1).strip()
                
                # Extract release date
                if not released_date:
                    date_match = re.search(r'(\d{4}-\d{2}-\d{2})', check_line)
                    if date_match:
                        released_date = date_match.group(1)
            
            # If we found a track URL, create track entry
            if track_url and title:
                # Clean up title (remove "Extended Mix", "Original Mix", etc.)
                title = re.sub(r'\s*(Extended Mix|Original Mix|Radio Edit|Instrumental Mix|Dub Mix|Remix).*$', '', title, flags=re.IGNORECASE)
                title = title.strip()
                
                track = TrackMeta(
                    title=title,
                    artists=artists,
                    label=label or '',
                    genre=genre or '',
                    bpm=bpm,
                    key=key or '',
                    released_date=released_date or '',
                    track_url=track_url
                )
                tracks.append(track)
        
        i += 1
    
    return tracks


def main():
    """Main function to scrape artist tracks using Firecrawl."""
    # Load config
    config = load_config()
    tracks_per_page = config.get("tracks_per_page", 50)
    a_level_labels = config.get("a_level_labels", [])
    
    # Define CSV paths
    os.makedirs("out", exist_ok=True)
    artists_csv = os.getenv("ARTISTS_CSV", "out/artists.csv")
    tracks_csv = os.getenv("TRACKS_CSV", "out/tracks.csv")
    
    # Define schemas
    artists_columns = ["artist_name", "beatport_url", "source_label", "created_at"]
    tracks_columns = [
        "title", "artists", "label", "label_tier", "genre", "bpm", "key",
        "released_date", "track_url", "source_page_type", "source_label",
        "source_artist", "created_at"
    ]
    
    # Load CSVs
    artists_df = load_or_create_csv(artists_csv, artists_columns)
    tracks_df = load_or_create_csv(tracks_csv, tracks_columns)
    
    # Filter artists with URLs
    artists_with_urls = artists_df[
        artists_df["beatport_url"].notna() &
        (artists_df["beatport_url"].astype(str).str.strip() != "") &
        (artists_df["beatport_url"].astype(str).str.strip() != "nan")
    ]
    
    print(f"Found {len(artists_with_urls)} artists with URLs")
    print(f"Processing first 100 artists to discover B-level labels...")
    print("(This will use Firecrawl MCP - make sure it's configured)\n")
    
    # Process first 100 artists (to get enough data for B-level discovery)
    artists_to_process = artists_with_urls.head(100)
    
    total_tracks = 0
    for idx, artist_row in artists_to_process.iterrows():
        artist_name = artist_row["artist_name"]
        artist_url = str(artist_row["beatport_url"]).strip()
        source_label = artist_row.get("source_label", "")
        
        print(f"Processing {idx+1}/{len(artists_to_process)}: {artist_name}")
        
        # Build tracks URL
        tracks_url = f"{artist_url}/tracks?page=1&per_page={tracks_per_page}"
        
        try:
            # Use Firecrawl MCP to scrape
            # Note: This needs to be called via MCP tools
            print(f"  Scraping with Firecrawl: {tracks_url}")
            
            # For now, we'll need to manually call Firecrawl or integrate it
            # This is a placeholder - the actual Firecrawl call would happen here
            print(f"  ⚠️  Firecrawl MCP integration needed")
            print(f"  ⚠️  Skipping for now - implement Firecrawl call")
            continue
            
            # Once Firecrawl is integrated, uncomment this:
            # markdown = firecrawl_scrape(url=tracks_url, formats=["markdown"], onlyMainContent=True)
            # tracks = parse_tracks_from_firecrawl_markdown(markdown, artist_name)
            
            # if tracks:
            #     new_tracks = []
            #     for track in tracks:
            #         track_dict = track.to_dict()
            #         track_dict["source_artist"] = artist_name
            #         track_dict["source_label"] = source_label
            #         track_dict["source_page_type"] = "artist_tracks"
            #         track_dict["label_tier"] = "unknown"
            #         new_tracks.append(track_dict)
            #     
            #     if new_tracks:
            #         new_tracks_df = pd.DataFrame(new_tracks)
            #         for col in tracks_columns:
            #             if col not in new_tracks_df.columns:
            #                 new_tracks_df[col] = None
            #         
            #         append_and_save(
            #             tracks_csv,
            #             new_tracks_df[tracks_columns],
            #             ["track_url"],
            #             deduplicate=True
            #         )
            #         total_tracks += len(new_tracks)
            #         print(f"  ✓ Found {len(new_tracks)} tracks")
        
        except Exception as e:
            print(f"  ✗ Error: {e}")
            continue
    
    print(f"\nDone! Total tracks added: {total_tracks}")
    print("\nNext step: Run classify_b_labels.py to find B-level labels")


if __name__ == "__main__":
    main()

