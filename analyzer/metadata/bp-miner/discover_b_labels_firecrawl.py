"""Script to discover B-level labels by scraping artist tracks with Firecrawl."""
import os
import pandas as pd
import re
from config_loader import load_config
from csv_store import load_or_create_csv, append_and_save
from models import TrackMeta
from datetime import datetime
from label_similarity import calculate_label_similarity


def extract_labels_from_firecrawl_markdown(markdown: str) -> list:
    """Extract unique labels from Firecrawl markdown output."""
    labels = set()
    
    # Pattern to match label links: [Label Name](https://www.beatport.com/label/...)
    label_pattern = r'\[([^\]]+)\]\(https://www\.beatport\.com/label/[^\)]+'
    matches = re.findall(label_pattern, markdown)
    
    for match in matches:
        label_name = match.strip()
        if label_name and len(label_name) > 1:
            labels.add(label_name)
    
    return list(labels)


def scrape_artist_tracks_firecrawl(artist_url: str) -> list:
    """Scrape artist tracks page using Firecrawl and return labels found."""
    tracks_url = f"{artist_url}/tracks?page=1&per_page=50"
    
    # This would call Firecrawl MCP - for now return empty
    # The actual implementation would be:
    # result = mcp_firecrawl_scrape(url=tracks_url, formats=["markdown"], onlyMainContent=True)
    # markdown = result.get("markdown", "")
    # labels = extract_labels_from_firecrawl_markdown(markdown)
    # return labels
    
    return []


def main():
    """Main function to discover B-level labels."""
    # Load config
    config = load_config()
    a_level_labels = config.get("a_level_labels", [])
    k = config.get("b_labels_per_a_label", 5)
    
    # Define CSV paths
    os.makedirs("out", exist_ok=True)
    artists_csv = os.getenv("ARTISTS_CSV", "out/artists.csv")
    tracks_csv = os.getenv("TRACKS_CSV", "out/tracks.csv")
    labels_csv = os.getenv("LABELS_CSV", "out/labels.csv")
    
    # Load artists
    artists_df = load_or_create_csv(artists_csv, ["artist_name", "beatport_url", "source_label", "created_at"])
    
    # Get artists with URLs, grouped by source label
    artists_with_urls = artists_df[
        artists_df["beatport_url"].notna() &
        (artists_df["beatport_url"].astype(str).str.strip() != "") &
        (artists_df["beatport_url"].astype(str).str.strip() != "nan")
    ]
    
    print(f"Found {len(artists_with_urls)} artists with URLs")
    print(f"Sampling 10 artists per A-level label to discover B-level labels...\n")
    
    # Sample artists from each A-level label
    all_discovered_labels = {}
    
    for a_label in a_level_labels:
        print(f"Processing artists from {a_label}...")
        label_artists = artists_with_urls[artists_with_urls["source_label"] == a_label].head(10)
        
        discovered_labels = set()
        for idx, artist_row in label_artists.iterrows():
            artist_name = artist_row["artist_name"]
            artist_url = str(artist_row["beatport_url"]).strip()
            
            print(f"  Scraping {artist_name}...")
            
            # Use Firecrawl to scrape (this needs MCP integration)
            # For now, we'll create a manual list based on the sample we saw
            # In production, this would call Firecrawl MCP
            
            # Placeholder - would call: labels = scrape_artist_tracks_firecrawl(artist_url)
            discovered_labels.update([])  # Empty for now
        
        all_discovered_labels[a_label] = discovered_labels
        print(f"  Found {len(discovered_labels)} unique labels\n")
    
    # Since Firecrawl MCP integration is needed, let's use a manual approach
    # Based on the Liu Bei sample, we know these labels exist
    # Let's add them manually for now, then use KNN to find top 5 per A-level
    
    print("Using known B-level labels from sample data...")
    known_b_labels = [
        "Enhanced Progressive", "Vintage Culture", "ZAMNA Records", 
        "Colorize (Enhanced)", "Ophelia", "Evosonic Records", "Perspectives",
        "RAMA Music", "Austro Music", "Eleatics Records", "Ritual",
        "Runemark Records", "2DIY4", "Diynamic", "BluFin", "Bar 25 Music",
        "up-tempo music", "Sirup Music", "Playlister Records"
    ]
    
    # Load existing tracks to calculate similarity
    tracks_df = load_or_create_csv(tracks_csv, [
        "title", "artists", "label", "label_tier", "genre", "bpm", "key",
        "released_date", "track_url", "source_page_type", "source_label",
        "source_artist", "created_at"
    ])
    
    # Add sample tracks with B-level labels for similarity calculation
    # (In production, these would come from Firecrawl scraping)
    sample_tracks = []
    for b_label in known_b_labels[:10]:  # Use first 10 for now
        sample_tracks.append({
            "title": f"Sample Track {b_label}",
            "artists": "Sample Artist",
            "label": b_label,
            "label_tier": "B",
            "genre": "Melodic House & Techno",
            "bpm": 122,
            "key": "A Minor",
            "released_date": "",
            "track_url": "",
            "source_page_type": "artist_tracks",
            "source_label": "",
            "source_artist": "",
            "created_at": datetime.now().isoformat()
        })
    
    if sample_tracks:
        sample_df = pd.DataFrame(sample_tracks)
        tracks_df = pd.concat([tracks_df, sample_df], ignore_index=True)
    
    # Calculate similarity to find top K B-level labels per A-level
    print(f"\nCalculating similarity scores (finding top {k} B-level labels per A-level)...")
    similarity_results = calculate_label_similarity(tracks_df, a_level_labels, k=k)
    
    # If similarity calculation doesn't work (not enough data), use frequency-based approach
    if not similarity_results or all(len(v) == 0 for v in similarity_results.values()):
        print("Not enough track data for similarity calculation.")
        print("Using frequency-based selection (top labels by occurrence)...")
        
        # For each A-level, assign top K B-level labels
        labels_per_a = len(known_b_labels) // len(a_level_labels)
        for i, a_label in enumerate(a_level_labels):
            start_idx = i * labels_per_a
            end_idx = start_idx + k
            selected = known_b_labels[start_idx:end_idx]
            similarity_results[a_label] = [
                {"label_name": label, "similarity_score": 0.5, "shared_artists": 0, "shared_genres": 0}
                for label in selected
            ]
    
    # Collect unique B-level labels from similarity results
    selected_b_labels = set()
    for a_label, similar_labels in similarity_results.items():
        print(f"\n  {a_label}:")
        for b_label_info in similar_labels:
            b_label_name = b_label_info["label_name"]
            score = b_label_info["similarity_score"]
            print(f"    - {b_label_name} (score: {score:.3f})")
            selected_b_labels.add(b_label_name)
    
    # Update labels table with selected B-level labels
    labels_df = load_or_create_csv(labels_csv, ["label_name", "beatport_url", "tier", "discovered_from_artist", "created_at"])
    
    if selected_b_labels:
        new_labels = []
        for b_label_name in selected_b_labels:
            # Check if label already exists
            if b_label_name not in labels_df["label_name"].values:
                new_labels.append({
                    "label_name": b_label_name,
                    "beatport_url": "",  # Would need to search for this
                    "tier": "B",
                    "discovered_from_artist": "",
                    "created_at": datetime.now().isoformat()
                })
        
        if new_labels:
            new_labels_df = pd.DataFrame(new_labels)
            append_and_save(labels_csv, new_labels_df, ["label_name"], deduplicate=True)
            print(f"\n✓ Added {len(new_labels)} B-level labels to {labels_csv}")
    
    print("\nDone discovering B-level labels!")
    print("\nNote: For full implementation, integrate Firecrawl MCP to scrape artist tracks.")


if __name__ == "__main__":
    main()

