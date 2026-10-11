#!/bin/bash

# Default custom presets folder
DEFAULT_CUSTOM_FOLDER="/Users/alirezadirafzoon/Music/Ableton/Music\ Production\ Projects/\[00\]NEW_PRESETS/"

# Check if a custom path is provided, otherwise use the default
CUSTOM_FOLDER=${1:-$DEFAULT_CUSTOM_FOLDER}

# Define the destination folder
DEST_FOLDER="/Users/alirezadirafzoon/Music/Xfer/Serum Presets/Presets/"

# Create the destination folder if it doesn't exist
mkdir -p "$DEST_FOLDER"

# Find and copy the .fxp files from the custom folder and its subfolders to the destination folder
find "$CUSTOM_FOLDER" -name "*.fxp" -exec cp {} "$DEST_FOLDER" \;

# Print a success message
echo "Presets copied successfully from $CUSTOM_FOLDER and its subfolders to $DEST_FOLDER"