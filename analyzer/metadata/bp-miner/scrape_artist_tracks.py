"""Script to scrape tracks from artist pages."""
import os
import sys
import pandas as pd
from config_loader import load_config
from csv_store import load_or_create_csv, append_and_save
from scraper_utils import fetch_html
from artist_scraper import search_artist_url, build_artist_tracks_url, parse_artist_tracks_page

# Try to use Firecrawl MCP if available
try:
    # Firecrawl MCP tools would be available via the MCP server
    # For now, we'll enhance the search with better parsing
    USE_FIRECRAWL = False  # Set to True if MCP Firecrawl is configured
except:
    USE_FIRECRAWL = False


def main(force_refresh: bool = False):
    """
    Main function to scrape artist tracks.
    
    Args:
        force_refresh: If True, re-scrape even if artist URL is already known.
    """
    # Load config
    config = load_config()
    tracks_per_page = config.get("tracks_per_page", 50)
    
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
    
    # Load CSVs (ensure tracks.csv exists even if empty)
    artists_df = load_or_create_csv(artists_csv, artists_columns)
    tracks_df = load_or_create_csv(tracks_csv, tracks_columns)
    
    # Ensure tracks.csv file exists (create empty if needed)
    if not os.path.exists(tracks_csv):
        empty_df = pd.DataFrame(columns=tracks_columns)
        empty_df.to_csv(tracks_csv, index=False)
    
    # Process all artists - those with URLs will use them, those without will search
    # Only skip if we already have tracks for them (unless force_refresh)
    artists_to_process = artists_df
    
    print(f"Processing {len(artists_to_process)} artists...")
    
    # Process each artist
    for idx, artist_row in artists_to_process.iterrows():
        artist_name = artist_row["artist_name"]
        source_label = artist_row.get("source_label", "")
        current_url = artist_row.get("beatport_url", "")
        
        # Handle NaN/None values
        if pd.isna(current_url):
            current_url = ""
        else:
            current_url = str(current_url).strip()
            # Handle "nan" string
            if current_url.lower() == "nan":
                current_url = ""
        
        print(f"\nProcessing artist: {artist_name}")
        
        # Search for artist URL only if we don't have one
        if not current_url:
            print(f"  Searching for artist URL...")
            artist_url = search_artist_url(artist_name)
            
            # If search failed, try extracting from label pages (already done in seed_artists)
            # The URL might have been extracted during Phase 1
            if not artist_url:
                # Check if we have the URL from seed_artists (should be in CSV already)
                # But if it's still empty, the search failed
                print(f"  Warning: Could not find URL for {artist_name}")
                # Skip this artist for now - we can't scrape without URL
                continue
            
            if artist_url:
                print(f"  Found URL: {artist_url}")
                # Update artist URL in CSV
                artists_df.loc[idx, "beatport_url"] = artist_url
                artists_df.to_csv(artists_csv, index=False)
        else:
            artist_url = current_url
        
        # Build tracks URL
        tracks_url = build_artist_tracks_url(artist_url, tracks_per_page)
        print(f"  Fetching tracks: {tracks_url}")
        
        # Fetch tracks page
        html = fetch_html(tracks_url)
        
        if not html:
            print(f"  Warning: Failed to fetch tracks page")
            continue
        
        # Parse tracks
        tracks = parse_artist_tracks_page(html, artist_name)
        print(f"  Found {len(tracks)} tracks")
        
        # Convert to DataFrame and add metadata
        new_tracks = []
        for track in tracks:
            track_dict = track.to_dict()
            track_dict["source_artist"] = artist_name
            track_dict["source_label"] = source_label
            track_dict["label_tier"] = "unknown"  # Will be classified later
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
            print(f"  Added {len(new_tracks)} tracks")
    
    print("\nDone scraping artist tracks!")
    
    # Build label frequency map
    tracks_df = load_or_create_csv(tracks_csv, tracks_columns)
    artist_tracks = tracks_df[tracks_df["source_page_type"] == "artist_tracks"]
    
    if not artist_tracks.empty:
        label_counts = artist_tracks["label"].value_counts()
        print("\nLabel frequency from artist tracks:")
        print(label_counts.head(20))


if __name__ == "__main__":
    force_refresh = "--force" in sys.argv
    main(force_refresh=force_refresh)

