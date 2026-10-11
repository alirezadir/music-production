"""Script to seed artists from A-level labels."""
import os
import sys
import re
from datetime import datetime
import pandas as pd
from bs4 import BeautifulSoup
from config_loader import load_config
from csv_store import load_or_create_csv, append_and_save
from scraper_utils import fetch_html
from label_scraper import parse_label_page_for_tracks, extract_artists_from_tracks


def main():
    """Main function to seed artists from A-level labels."""
    # Load config
    config = load_config()
    a_level_label_urls = config.get("a_level_label_urls", {})
    
    # Define CSV paths
    os.makedirs("out", exist_ok=True)
    artists_csv = os.getenv("ARTISTS_CSV", "out/artists.csv")
    labels_csv = os.getenv("LABELS_CSV", "out/labels.csv")
    tracks_csv = os.getenv("TRACKS_CSV", "out/tracks.csv")
    
    # Define schemas
    artists_columns = ["artist_name", "beatport_url", "source_label", "created_at"]
    # Note: labels.csv now uses B-level format, A-level labels are stored separately if needed
    # For now, we'll skip adding A-level labels to labels.csv in Phase 1
    tracks_columns = [
        "title", "artists", "label", "label_tier", "genre", "bpm", "key",
        "released_date", "track_url", "source_page_type", "source_label",
        "source_artist", "created_at"
    ]
    
    # Load or create CSVs
    artists_df = load_or_create_csv(artists_csv, artists_columns)
    # labels.csv is now for B-level labels only, so we skip it in Phase 1
    tracks_df = load_or_create_csv(tracks_csv, tracks_columns)
    
    # Process each A-level label
    for label_name, label_url in a_level_label_urls.items():
        print(f"Processing A-level label: {label_name}")
        
        # Note: A-level labels are not added to labels.csv anymore
        # labels.csv is now for B-level labels with associated A-level format
        # A-level labels are stored in config.json
        
        # Fetch label page
        print(f"  Fetching: {label_url}")
        html = fetch_html(label_url)
        
        if not html:
            print(f"  Warning: Failed to fetch {label_url}")
            continue
        
        # Parse tracks from main label page
        tracks = parse_label_page_for_tracks(html, label_name)
        print(f"  Found {len(tracks)} tracks from label page")
        
        # Also fetch tracks from label tracks page for more diversity
        from label_scraper import build_label_tracks_url, parse_label_tracks_page
        tracks_url = build_label_tracks_url(label_url, config.get("tracks_per_page", 50))
        print(f"  Fetching tracks page: {tracks_url}")
        tracks_html = fetch_html(tracks_url)
        
        if tracks_html:
            tracks_page_tracks = parse_label_tracks_page(tracks_html, label_name)
            print(f"  Found {len(tracks_page_tracks)} tracks from tracks page")
            # Combine tracks (deduplication will happen later)
            tracks.extend(tracks_page_tracks)
        
        # Save tracks to CSV (from label pages)
        if tracks:
            new_tracks = []
            for track in tracks:
                track_dict = track.to_dict()
                track_dict["label_tier"] = "A"  # These are from A-level labels
                track_dict["source_page_type"] = "label_tracks"  # From label page
                track_dict["source_label"] = label_name
                track_dict["source_artist"] = ""  # Not from specific artist
                new_tracks.append(track_dict)
            
            if new_tracks:
                new_tracks_df = pd.DataFrame(new_tracks)
                # Ensure all columns exist
                for col in tracks_columns:
                    if col not in new_tracks_df.columns:
                        new_tracks_df[col] = None
                
                # Append to tracks CSV
                append_and_save(
                    tracks_csv,
                    new_tracks_df[tracks_columns],
                    ["track_url"],  # Use track_url as deduplication key
                    deduplicate=True
                )
                print(f"  Saved {len(new_tracks)} tracks to tracks.csv")
        
        # Extract artists and their URLs from tracks
        artists = extract_artists_from_tracks(tracks)
        print(f"  Found {len(artists)} unique artists")
        
        # Extract artist URLs from the label page HTML
        from bs4 import BeautifulSoup
        
        soup = BeautifulSoup(html, "html.parser")
        artist_url_map = {}  # artist_name -> url
        
        # Find all artist links in HTML - try multiple strategies
        artist_links = soup.find_all("a", href=re.compile("/artist/"))
        
        for link in artist_links:
            href = link.get("href", "")
            if not href:
                continue
            
            # Get link text - try multiple ways
            link_text = link.get_text(strip=True)
            if not link_text:
                # Try getting from title attribute
                link_text = link.get("title", "")
            if not link_text:
                # Try getting from alt text of image
                img = link.find("img")
                if img:
                    link_text = img.get("alt", "") or img.get("title", "")
            if not link_text:
                # Try getting from data attributes
                link_text = link.get("data-ec-name", "") or link.get("data-artist-name", "")
            
            if href and link_text:
                # Normalize URL
                if href.startswith("/"):
                    full_url = f"https://www.beatport.com{href}"
                elif href.startswith("http"):
                    full_url = href
                else:
                    full_url = f"https://www.beatport.com/{href}"
                
                # Store with normalized key (case-insensitive)
                key = link_text.strip()
                artist_url_map[key] = full_url
                # Also store lowercase version for matching
                artist_url_map[key.lower()] = full_url
        
        # Add artists to CSV
        new_artists = []
        for artist_name in artists:
            # Check if artist already exists
            if artist_name not in artists_df["artist_name"].values:
                # Try to find URL from the map we extracted
                artist_url = artist_url_map.get(artist_name, "")
                # Also try case-insensitive match
                if not artist_url:
                    for key, url in artist_url_map.items():
                        if key.lower() == artist_name.lower():
                            artist_url = url
                            break
                
                new_artists.append({
                    "artist_name": artist_name,
                    "beatport_url": artist_url,
                    "source_label": label_name,
                    "created_at": datetime.now().isoformat()
                })
        
        if new_artists:
            new_artists_df = pd.DataFrame(new_artists)
            append_and_save(artists_csv, new_artists_df, ["artist_name"], deduplicate=True)
            print(f"  Added {len(new_artists)} new artists")
            # Reload to update in-memory DataFrame
            artists_df = load_or_create_csv(artists_csv, artists_columns)
    
    print("Done seeding artists from A-level labels!")


if __name__ == "__main__":
    main()

