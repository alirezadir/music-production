import os
import pandas as pd
import re
from collections import Counter

# Define the root directory
root_dir = "/path/to/samples-and-presets"

# File type categories
file_categories = {
    "samples": [".wav", ".mp3", ".aif"],
    "presets": [".fxp", ".nmsv", ".adg"],
    "midi": [".mid", ".midi"]
}

# Keywords for subcategories with case sensitivity
subcategories = {
    "Hihats": ["hihat", "HH"],
    "Claps": ["clap"],
    "Kicks": ["kick"],
    "Drum Loops": ["loop"],
    "Vocals": ["vocal", "acapella", "vox"],
    "FX": ["impact", "sweep", "rise", "fall"],
    "Bass": ["bass"],
    "Synth": ["synth", "lead", "pad", "pluck"]
}

# Initialize data collection
data = []

def extract_tags(filename):
    """Extract tags from filenames based on keywords."""
    tags = []
    for category, keywords in subcategories.items():
        if any(re.search(rf"\b{keyword}\b", filename) for keyword in keywords):
            tags.append(category)
    return tags

def extract_bpm_and_key(filename):
    """Extract BPM and musical key from filenames."""
    bpm = None
    key = None

    # Look for BPM (e.g., 120bpm or just numbers that likely represent tempo)
    bpm_match = re.search(r"\b(\d{2,3})\b", filename)
    if bpm_match:
        bpm = int(bpm_match.group(1))

    # Look for musical keys (e.g., Cmaj, Dmin, G#)
    key_match = re.search(r"\b([A-Ga-g](#|b)?(maj|min)?)\b", filename)
    if key_match:
        key = key_match.group(0)

    return bpm, key

# Walk through the directory
for subdir, _, files in os.walk(root_dir):
    for file in files:
        filepath = os.path.join(subdir, file)
        file_ext = os.path.splitext(file)[1].lower()
        file_size = os.path.getsize(filepath)

        # Determine file category
        category = None
        for cat, exts in file_categories.items():
            if file_ext in exts:
                category = cat
                break

        # Skip unrecognized files
        if not category:
            continue

        # Extract tags and metadata
        tags = extract_tags(file)
        bpm, key = extract_bpm_and_key(file)

        # Collect data
        data.append({
            "filepath": filepath,
            "category": category,
            "tags": ", ".join(tags),
            "size_kb": file_size / 1024,
            "bpm": bpm,
            "key": key
        })

# Create a DataFrame
df = pd.DataFrame(data)

# Display basic statistics
print("File Counts by Category:")
print(df["category"].value_counts())
print("\nTag Counts:")
print(Counter(tag for tags in df["tags"] for tag in tags.split(", ")))

# Save to CSV for further analysis
df.to_csv("sample_preset_analysis.csv", index=False)

# Display the first few rows
df.head()
