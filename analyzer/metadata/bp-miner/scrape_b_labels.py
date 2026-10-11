"""Script to scrape tracks from B-level labels."""
import os
import pandas as pd
from config_loader import load_config
from csv_store import load_or_create_csv, append_and_save
from scraper_utils import fetch_html
from label_scraper import (
    search_label_url,
    build_label_tracks_url,
    parse_label_top10,
    parse_label_tracks_page
)


def main():
    """Main function to scrape B-level label tracks."""
    # Load config
    config = load_config()
    tracks_per_page = config.get("tracks_per_page", 50)
    
    # Define CSV paths
    os.makedirs("out", exist_ok=True)
    labels_csv = os.getenv("LABELS_CSV", "out/labels.csv")
    tracks_csv = os.getenv("TRACKS_CSV", "out/tracks.csv")
    
    # Define schemas
    labels_columns = ["label_name", "beatport_url", "tier", "discovered_from_artist", "created_at"]
    tracks_columns = [
        "title", "artists", "label", "label_tier", "genre", "bpm", "key",
        "released_date", "track_url", "source_page_type", "source_label",
        "source_artist", "created_at"
    ]
    
    # Load CSVs
    labels_df = load_or_create_csv(labels_csv, labels_columns)
    tracks_df = load_or_create_csv(tracks_csv, tracks_columns)
    
    # Filter B-level labels
    b_labels = labels_df[labels_df["tier"] == "B"]
    
    if b_labels.empty:
        print("No B-level labels found. Run classify_b_labels.py first.")
        return
    
    print(f"Processing {len(b_labels)} B-level labels...")
    
    # Process each B-level label
    for idx, label_row in b_labels.iterrows():
        label_name = label_row["label_name"]
        current_url = label_row.get("beatport_url", "")
        
        # Handle NaN/None values
        if pd.isna(current_url):
            current_url = ""
        else:
            current_url = str(current_url).strip()
        
        print(f"\nProcessing B-level label: {label_name}")
        
        # Search for label URL if needed
        if not current_url or current_url == "":
            print(f"  Searching for label URL...")
            label_url = search_label_url(label_name)
            
            if label_url:
                print(f"  Found URL: {label_url}")
                # Update label URL in CSV
                labels_df.loc[idx, "beatport_url"] = label_url
                labels_df.to_csv(labels_csv, index=False)
            else:
                print(f"  Warning: Could not find URL for {label_name}")
                continue
        else:
            label_url = current_url
        
        # Fetch label profile page (for Top 10)
        print(f"  Fetching label profile: {label_url}")
        profile_html = fetch_html(label_url)
        
        top10_tracks = []
        if profile_html:
            top10_tracks = parse_label_top10(profile_html, label_name)
            print(f"  Found {len(top10_tracks)} Top 10 tracks")
        
        # Fetch label tracks page
        tracks_url = build_label_tracks_url(label_url, tracks_per_page)
        print(f"  Fetching tracks page: {tracks_url}")
        
        tracks_html = fetch_html(tracks_url)
        
        label_tracks = []
        if tracks_html:
            label_tracks = parse_label_tracks_page(tracks_html, label_name)
            print(f"  Found {len(label_tracks)} tracks from tracks page")
        
        # Combine all tracks
        all_tracks = []
        
        # Add top10 tracks with proper metadata
        for track in top10_tracks:
            track_dict = track.to_dict()
            track_dict["label_tier"] = "B"
            track_dict["source_page_type"] = "label_top10"
            all_tracks.append(track_dict)
        
        # Add label tracks with proper metadata
        for track in label_tracks:
            track_dict = track.to_dict()
            track_dict["label_tier"] = "B"
            track_dict["source_page_type"] = "label_tracks"
            all_tracks.append(track_dict)
        
        new_tracks = all_tracks
        
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
    
    print("\nDone scraping B-level label tracks!")


if __name__ == "__main__":
    main()

