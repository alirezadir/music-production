"""Script to classify B-level labels from scraped tracks using KNN similarity."""
import os
import pandas as pd
from config_loader import load_config
from csv_store import load_or_create_csv, append_and_save
from label_classifier import infer_b_labels
from label_similarity import calculate_label_similarity
from datetime import datetime


def main():
    """Main function to classify B-level labels using KNN similarity."""
    # Load config
    config = load_config()
    exclude_labels = config.get("exclude_labels", [])
    a_level_labels = config.get("a_level_labels", [])
    k = config.get("b_labels_per_a_label", 5)
    
    # Define CSV paths
    os.makedirs("out", exist_ok=True)
    tracks_csv = os.getenv("TRACKS_CSV", "out/tracks.csv")
    labels_csv = os.getenv("LABELS_CSV", "out/labels.csv")
    
    # Define schemas
    tracks_columns = [
        "title", "artists", "label", "label_tier", "genre", "bpm", "key",
        "released_date", "track_url", "source_page_type", "source_label",
        "source_artist", "created_at"
    ]
    from labels_schema import LABELS_B_SCHEMA
    labels_columns = LABELS_B_SCHEMA
    
    # Load CSVs
    tracks_df = load_or_create_csv(tracks_csv, tracks_columns)
    labels_df = load_or_create_csv(labels_csv, labels_columns)
    
    if tracks_df.empty:
        print("No tracks found. Run scrape_artist_tracks.py first.")
        return
    
    print(f"Analyzing {len(tracks_df)} tracks...")
    
    # First, infer all potential B-level labels
    b_labels_df = infer_b_labels(tracks_df, exclude_labels)
    
    if b_labels_df.empty:
        print("No B-level labels found.")
        return
    
    print(f"\nFound {len(b_labels_df)} potential B-level labels")
    
    # Calculate similarity to find top K B-level labels per A-level
    print(f"\nCalculating similarity scores (finding top {k} B-level labels per A-level)...")
    similarity_results = calculate_label_similarity(tracks_df, a_level_labels, k=k)
    
    # Collect unique B-level labels from similarity results
    selected_b_labels = set()
    for a_label, similar_labels in similarity_results.items():
        print(f"\n  {a_label}:")
        for b_label_info in similar_labels:
            b_label_name = b_label_info["label_name"]
            score = b_label_info["similarity_score"]
            shared_artists = b_label_info["shared_artists"]
            shared_genres = b_label_info["shared_genres"]
            print(f"    - {b_label_name} (score: {score:.3f}, shared artists: {shared_artists}, shared genres: {shared_genres})")
            selected_b_labels.add(b_label_name)
    
    # Update labels table with selected B-level labels
    # Group by associated A-level label
    if selected_b_labels and similarity_results:
        new_labels = []
        for a_label, similar_labels in similarity_results.items():
            for b_label_info in similar_labels:
                b_label_name = b_label_info["label_name"]
                # Check if label already exists for this A-level
                exists = (labels_df["b_label_name"] == b_label_name) & \
                        (labels_df["associated_a_label"] == a_label)
                if not exists.any():
                    new_labels.append({
                        "b_label_name": b_label_name,
                        "associated_a_label": a_label,
                        "primary_genre": "",
                        "secondary_genres": "",
                        "example_artists": "",
                        "relationship_reason": f"Similarity score: {b_label_info['similarity_score']:.3f}",
                        "beatport_url": ""
                    })
        
        if new_labels:
            new_labels_df = pd.DataFrame(new_labels)
            append_and_save(labels_csv, new_labels_df, ["b_label_name", "associated_a_label"], deduplicate=True)
            print(f"\nAdded {len(new_labels)} B-level labels to {labels_csv}")
    
    print("\nDone classifying B-level labels!")


if __name__ == "__main__":
    main()

