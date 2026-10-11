"""Script to clean and deduplicate all CSV files."""
import os
import pandas as pd
from csv_store import load_or_create_csv
from cleaning import (
    normalize_label_name,
    normalize_artist_name,
    normalize_track_row,
    deduplicate_tracks
)


def main():
    """Main function to clean all CSV files."""
    # Define CSV paths
    os.makedirs("out", exist_ok=True)
    artists_csv = os.getenv("ARTISTS_CSV", "out/artists.csv")
    labels_csv = os.getenv("LABELS_CSV", "out/labels.csv")
    tracks_csv = os.getenv("TRACKS_CSV", "out/tracks.csv")
    
    # Define schemas
    artists_columns = ["artist_name", "beatport_url", "source_label", "created_at"]
    from labels_schema import LABELS_B_SCHEMA
    labels_columns = LABELS_B_SCHEMA
    tracks_columns = [
        "title", "artists", "label", "label_tier", "genre", "bpm", "key",
        "released_date", "track_url", "source_page_type", "source_label",
        "source_artist", "created_at"
    ]
    
    print("Cleaning artists.csv...")
    # Load and clean artists
    artists_df = load_or_create_csv(artists_csv, artists_columns)
    if not artists_df.empty:
        artists_df["artist_name"] = artists_df["artist_name"].apply(normalize_artist_name)
        artists_df["source_label"] = artists_df["source_label"].apply(normalize_label_name)
        # Deduplicate by artist_name
        artists_df = artists_df.drop_duplicates(subset=["artist_name"], keep="first")
        artists_df.to_csv(artists_csv, index=False)
        print(f"  Cleaned {len(artists_df)} artists")
    
    print("Cleaning labels.csv...")
    # Load and clean labels (new B-level format)
    labels_df = load_or_create_csv(labels_csv, labels_columns)
    if not labels_df.empty:
        if "b_label_name" in labels_df.columns:
            labels_df["b_label_name"] = labels_df["b_label_name"].apply(normalize_label_name)
        if "associated_a_label" in labels_df.columns:
            labels_df["associated_a_label"] = labels_df["associated_a_label"].apply(normalize_label_name)
        # Deduplicate by b_label_name and associated_a_label
        if "b_label_name" in labels_df.columns and "associated_a_label" in labels_df.columns:
            labels_df = labels_df.drop_duplicates(subset=["b_label_name", "associated_a_label"], keep="first")
        labels_df.to_csv(labels_csv, index=False)
        print(f"  Cleaned {len(labels_df)} B-level labels")
    
    print("Cleaning tracks.csv...")
    # Load and clean tracks
    tracks_df = load_or_create_csv(tracks_csv, tracks_columns)
    if not tracks_df.empty:
        # Normalize each row
        normalized_rows = []
        for _, row in tracks_df.iterrows():
            normalized_row = normalize_track_row(row.to_dict())
            normalized_rows.append(normalized_row)
        
        tracks_df = pd.DataFrame(normalized_rows)
        
        # Deduplicate
        original_count = len(tracks_df)
        tracks_df = deduplicate_tracks(tracks_df)
        removed_count = original_count - len(tracks_df)
        
        # Ensure column order
        tracks_df = tracks_df[tracks_columns]
        tracks_df.to_csv(tracks_csv, index=False)
        print(f"  Cleaned {len(tracks_df)} tracks (removed {removed_count} duplicates)")
    
    print("\nDone cleaning all CSV files!")
    print("\nNext step: Run sync_all_to_sheets.py to sync to Google Sheets.")


if __name__ == "__main__":
    main()

