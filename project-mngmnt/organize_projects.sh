#!/bin/bash

# Define the source directory where your Ableton projects are scattered
SRC_DIR="/path/to/your/ableton/projects"  # Replace with your source directory path

# Define the destination directory where you want to organize the projects
DEST_DIR="/path/to/your/organized/projects"  # Replace with your destination directory path

# Function to get the year from the file's creation date
get_year() {
  local file="$1"
  date -r "$file" +"%Y"
}

# Function to get the category based on the project name
get_category() {
  local project_name="$1"
  if [[ "$project_name" == *Album* ]]; then
    echo "Albums"
  elif [[ "$project_name" == *EP* ]]; then
    echo "EPs"
  elif [[ "$project_name" == *Colab* ]]; then
    echo "Colabs"
  else
    echo "Singles"
  fi
}

# Create the destination directory if it doesn't exist
mkdir -p "$DEST_DIR"

# Find all Ableton project files (.als) in the source directory
find "$SRC_DIR" -type f -name "*.als" | while read -r project_file; do
  # Get the year from the project file's creation date
  year=$(get_year "$project_file")

  # Extract the project name (without extension) from the project file path
  project_name=$(basename "$project_file" .als)

  # Determine the category based on the project name
  category=$(get_category "$project_name")

  # Create the project directory structure in the destination directory
  project_dir="$DEST_DIR/$year/$category/$project_name"
  mkdir -p "$project_dir/Samples" "$project_dir/Recordings"

  # Move the project file to the project directory
  mv "$project_file" "$project_dir/"

  # Find and move sample files associated with the project
  find "$SRC_DIR" -type f \( -iname "*.wav" -o -iname "*.aiff" \) -path "*/$project_name/*" -exec mv {} "$project_dir/Samples/" \;

  # Find and move recording files associated with the project
  find "$SRC_DIR" -type f \( -iname "*.wav" -o -iname "*.aiff" \) -path "*/Recordings/*" -exec mv {} "$project_dir/Recordings/" \;
  
  echo "Organized $project_file into $project_dir"
done