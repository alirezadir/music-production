#!/bin/bash

# Script to remove all .asd files in a directory and its subdirectories

echo "Enter the directory to clean up (default: current directory):"
read target_dir

# Use current directory if none provided
if [ -z "$target_dir" ]; then
    target_dir="$(pwd)"
fi

# Confirm action
echo "Are you sure you want to delete all .asd files in '$target_dir' and its subdirectories? (y/n)"
read confirmation

if [[ "$confirmation" != "y" ]]; then
    echo "Operation canceled."
    exit 1
fi

# Find and delete all .asd files
find "$target_dir" -type f -name "*.asd" -exec rm -v {} \;

echo "Cleanup complete!"
