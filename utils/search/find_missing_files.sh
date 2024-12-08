#!/bin/bash

# Directory where your samples are stored
sample_dir="/Volumes/MUSICALLY/[01]MUSIC-PROD:SRC/[01]SOUNDBANK_DEER"

# List of missing file names (replace these with the actual missing file names from your screenshot)
missing_files=(
  "missing_file_name_1.wav"
  "missing_file_name_2.aif"
  "missing_file_name_3.wav"
  # Add more file names as needed
)

# Loop through the list of missing files and search for each one
for file in "${missing_files[@]}"; do
  echo "Searching for: $file"
  sudo find "$sample_dir" -type f -name "$file"
done