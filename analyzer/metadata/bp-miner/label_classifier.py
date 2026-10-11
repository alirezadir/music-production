"""Label classification utilities."""
import pandas as pd
from typing import List
from csv_store import load_or_create_csv, append_and_save
from datetime import datetime


def infer_b_labels(tracks_df: pd.DataFrame, exclude_labels: List[str]) -> pd.DataFrame:
    """
    Infer B-level labels from tracks, excluding A-level labels.
    
    Args:
        tracks_df: DataFrame with track data.
        exclude_labels: List of label names to exclude (A-level labels).
    
    Returns:
        DataFrame with inferred B-level labels.
    """
    # Use all tracks (not just artist_tracks) to find labels
    # This includes tracks from label pages which may have different labels
    all_tracks = tracks_df[tracks_df["label"].notna() & (tracks_df["label"] != "")]
    
    if all_tracks.empty:
        return pd.DataFrame(columns=["label_name", "count"])
    
    # Get label counts from all tracks
    label_counts = all_tracks["label"].value_counts().reset_index()
    label_counts.columns = ["label_name", "count"]
    
    # Normalize exclude labels (case-insensitive)
    exclude_lower = [label.lower().strip() for label in exclude_labels]
    
    # Filter out excluded labels
    def should_exclude(label):
        if pd.isna(label) or label == "":
            return True
        return label.lower().strip() in exclude_lower
    
    b_labels = label_counts[~label_counts["label_name"].apply(should_exclude)]
    
    return b_labels


def update_labels_table(b_labels_df: pd.DataFrame, labels_csv: str = "out/labels.csv") -> None:
    """
    Update labels.csv with inferred B-level labels.
    
    Args:
        b_labels_df: DataFrame with B-level labels (must have 'label_name' column).
        labels_csv: Path to labels CSV file.
    """
    if b_labels_df.empty:
        return
    
    labels_columns = ["label_name", "beatport_url", "tier", "discovered_from_artist", "created_at"]
    labels_df = load_or_create_csv(labels_csv, labels_columns)
    
    # Prepare new label rows
    new_labels = []
    for _, row in b_labels_df.iterrows():
        label_name = row["label_name"]
        
        # Check if label already exists
        if label_name not in labels_df["label_name"].values:
            new_labels.append({
                "label_name": label_name,
                "beatport_url": "",
                "tier": "B",
                "discovered_from_artist": "",  # Could aggregate artist info here
                "created_at": datetime.now().isoformat()
            })
    
    if new_labels:
        new_labels_df = pd.DataFrame(new_labels)
        append_and_save(labels_csv, new_labels_df, ["label_name"], deduplicate=True)
        print(f"Added {len(new_labels)} new B-level labels to {labels_csv}")

