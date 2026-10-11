"""Schema definitions for labels CSV files."""
# New schema for labels.csv (B-level labels with associated A-level)
LABELS_B_SCHEMA = [
    "b_label_name",
    "associated_a_label", 
    "primary_genre",
    "secondary_genres",
    "example_artists",
    "relationship_reason",
    "beatport_url"
]

# Old schema (for backward compatibility if needed)
LABELS_OLD_SCHEMA = [
    "label_name",
    "beatport_url",
    "tier",
    "discovered_from_artist",
    "created_at"
]

