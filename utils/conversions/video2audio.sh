#!/bin/bash

# Check if input directory is provided
if [ -z "$1" ]; then
    echo "Usage: $0 <input_directory>"
    exit 1
fi

INPUT_DIR="$1"
OUTPUT_DIR="$INPUT_DIR/Audio"

# Create Audio directory if it doesn't exist
mkdir -p "$OUTPUT_DIR"

# Convert each video file in the input directory and its subdirectories
find "$INPUT_DIR" -type f -name "*.mp4" -print0 | while IFS= read -r -d $'\0' file; do
    # Get the filename without the directory path and extension
    filename=$(basename "$file")
    filename_no_ext="${filename%.*}"

    # Construct the output audio file path
    output_audio="$OUTPUT_DIR/$filename_no_ext.wav"

    # Check if the output file already exists, skip conversion if it does
    if [ ! -e "$output_audio" ]; then
        ffmpeg -i "$file" -vn -ar 44100 -ac 2 -b:a 192k "$output_audio"
    else
        echo "Skipping $file: Audio file $output_audio already exists."
    fi
done