#!/bin/bash

# Define the source and destination directories
SRC_DIR="/path/to/your/music/source"  # Replace with your source directory path
DEST_DIR="/path/to/your/music/destination"  # Replace with your destination directory path

# Create an associative array to keep track of file hashes
declare -A file_hashes

# Function to calculate the hash of a file
calculate_hash() {
  local file="$1"
  md5 -q "$file"
}

# Function to get the year and month from the file's creation date
get_year_month() {
  local file="$1"
  date -r "$file" +"%Y/%m"
}

# Function to organize and move files
organize_files() {
  local src_dir="$1"
  local dest_dir="$2"

  # Find all music files in the source directory
  find "$src_dir" -type f \( -iname "*.mp3" -o -iname "*.wav" -o -iname "*.aiff" \) | while read -r file; do
    # Calculate the file's hash
    file_hash=$(calculate_hash "$file")

    # Check if the file hash is already in the array (duplicate check)
    if [[ -v file_hashes["$file_hash"] ]]; then
      echo "Duplicate found: $file"
      continue
    fi

    # Add the file hash to the array
    file_hashes["$file_hash"]="$file"

    # Get the year and month from the file's creation date
    year_month=$(get_year_month "$file")

    # Create the destination directory if it doesn't exist
    dest_path="$dest_dir/$year_month"
    mkdir -p "$dest_path"

    # Move the file to the destination directory
    mv "$file" "$dest_path/"
    echo "Moved $file to $dest_path/"
  done
}

# Run the organize_files function
organize_files "$SRC_DIR" "$DEST_DIR"