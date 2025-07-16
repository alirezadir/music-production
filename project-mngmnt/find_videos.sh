#!/bin/bash

# Root directory and output file
root_directory=${1:-.}
output_file="video_files_list.txt"

# Find video files and save to output file
find "$root_directory" -type f \( -iname "*.mp4" -o -iname "*.mov" \) > "$output_file"

# Show results
echo "Video files saved to $output_file"
cat "$output_file"