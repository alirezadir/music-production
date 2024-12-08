#!/bin/bash

# # Define the input directory
# INPUT_DIRECTORY="/Volumes/MUSICALLY/[01]MUSIC-PROD:SRC/[01]SOUNDBANK_DEER/[2023-4]REF-TRACKS/[01]REF-Tracks/ToStem"

# # Run the Python script with the specified input directory
# python3 process_stems.py "$INPUT_DIRECTORY"

# Define the input directory
INPUT_DIRECTORY="/Volumes/MUSICALLY/[01]MUSIC-PROD:SRC/[01]SOUNDBANK_DEER/[2023-4]REF-TRACKS/[01]REF-Tracks/ToStem"

# Loop through the .mp3 files and call the Python script for each
for file in "$INPUT_DIRECTORY"/*.mp3; do
  if [ -e "$file" ]; then
    python3 process_stems.py "$file"
  else
    echo "No .mp3 files found in the directory."
  fi
done