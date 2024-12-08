#!/bin/bash

# Define source and destination directories
SRC_DIR="/Users/alirezadirafzoon/Music/Beats"  # Replace with your source directory path
DEST_DIR="/Users/alirezadirafzoon/Music/DJLib"  # Replace with your destination directory path


# Create a temporary file to track file hashes
TEMP_FILE_HASHES="/tmp/file_hashes.txt"
> "$TEMP_FILE_HASHES"

# Function to calculate the hash of a file
calculate_hash() {
    local file="$1"
    md5 -q "$file"
}

# Create destination directories if they don't exist
mkdir -p "$DEST_DIR"

# Find all music files and organize them
find "$SRC_DIR" -type f \( -iname "*.mp3" -o -iname "*.wav" -o -iname "*.aiff" \) | while read -r file; do
    # Calculate the file's hash
    file_hash=$(calculate_hash "$file")

    # Check if the file hash already exists
    if grep -q "$file_hash" "$TEMP_FILE_HASHES"; then
        echo "Duplicate found and removed: $file"
        rm "$file"
        continue
    fi

    # Add the file hash to the temporary file
    echo "$file_hash" >> "$TEMP_FILE_HASHES"

    # Get the file's creation date
    creation_date=$(stat -f "%SB" -t "%Y/%m" "$file")

    # Create the destination directory based on the creation date
    dest_dir="$DEST_DIR/$creation_date"
    mkdir -p "$dest_dir"

    # Move the file to the destination directory
    mv "$file" "$dest_dir/"
    echo "Moved $file to $dest_dir/"
done

# Clean up the temporary file
rm "$TEMP_FILE_HASHES"