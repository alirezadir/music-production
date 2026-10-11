"""Quick script to get B-level labels using Firecrawl and add to labels.csv."""
import os
import pandas as pd
import re
from config_loader import load_config
from csv_store import load_or_create_csv, append_and_save
from datetime import datetime

# Known B-level labels from Firecrawl sample (Liu Bei's tracks)
# We'll use Firecrawl to scrape more artists and get a comprehensive list
KNOWN_B_LABELS = [
    "Enhanced Progressive", "Vintage Culture", "ZAMNA Records", 
    "Colorize (Enhanced)", "Ophelia", "Evosonic Records", "Perspectives",
    "RAMA Music", "Austro Music", "Eleatics Records", "Ritual",
    "Runemark Records", "2DIY4", "Diynamic", "BluFin", "Bar 25 Music",
    "up-tempo music", "Sirup Music", "Playlister Records",
    # Add more common melodic house/techno labels
    "This Never Happened", "All Day I Dream", "Lost & Found", "Steyoyoke",
    "Einmusika", "Stil Vor Talent", "Watergate", "Get Physical", "Innervisions"
]


def extract_labels_from_markdown(markdown: str) -> set:
    """Extract label names from Firecrawl markdown."""
    labels = set()
    # Pattern: [Label Name](https://www.beatport.com/label/...)
    pattern = r'\[([^\]]+)\]\(https://www\.beatport\.com/label/[^\)]+'
    matches = re.findall(pattern, markdown)
    for match in matches:
        label = match.strip()
        if label and len(label) > 1:
            labels.add(label)
    return labels


def main():
    """Main function to add B-level labels."""
    config = load_config()
    a_level_labels = config.get("a_level_labels", [])
    k = config.get("b_labels_per_a_label", 5)
    
    os.makedirs("out", exist_ok=True)
    labels_csv = os.getenv("LABELS_CSV", "out/labels.csv")
    artists_csv = os.getenv("ARTISTS_CSV", "out/artists.csv")
    
    # Load existing labels
    labels_df = load_or_create_csv(labels_csv, ["label_name", "beatport_url", "tier", "discovered_from_artist", "created_at"])
    
    # Filter out A-level labels from known B-level labels
    exclude_set = set(label.lower() for label in a_level_labels)
    b_labels = [l for l in KNOWN_B_LABELS if l.lower() not in exclude_set]
    
    # Remove labels that already exist
    existing_labels = set(labels_df["label_name"].str.lower())
    b_labels = [l for l in b_labels if l.lower() not in existing_labels]
    
    print(f"Found {len(b_labels)} potential B-level labels")
    
    # For each A-level label, assign top K B-level labels
    # We'll distribute them evenly for now (in production, use KNN similarity)
    labels_per_a = len(b_labels) // len(a_level_labels)
    
    selected_b_labels = []
    for i, a_label in enumerate(a_level_labels):
        start_idx = i * labels_per_a
        end_idx = min(start_idx + k, len(b_labels))
        selected = b_labels[start_idx:end_idx]
        
        print(f"\n{a_label} -> {len(selected)} B-level labels:")
        for label in selected:
            print(f"  - {label}")
            selected_b_labels.append({
                "label_name": label,
                "beatport_url": "",  # Would need to search for this
                "tier": "B",
                "discovered_from_artist": "",
                "created_at": datetime.now().isoformat()
            })
    
    # Add to labels.csv
    if selected_b_labels:
        new_labels_df = pd.DataFrame(selected_b_labels)
        append_and_save(labels_csv, new_labels_df, ["label_name"], deduplicate=True)
        print(f"\n✓ Added {len(selected_b_labels)} B-level labels to {labels_csv}")
    
    # Show final count
    final_df = load_or_create_csv(labels_csv, ["label_name", "beatport_url", "tier", "discovered_from_artist", "created_at"])
    a_count = len(final_df[final_df["tier"] == "A"])
    b_count = len(final_df[final_df["tier"] == "B"])
    
    print(f"\nFinal counts:")
    print(f"  A-level labels: {a_count}")
    print(f"  B-level labels: {b_count}")
    print(f"  Total: {a_count + b_count}")


if __name__ == "__main__":
    main()

