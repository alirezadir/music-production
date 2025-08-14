#!/bin/bash
# Delete all .asd files using find command

echo "Deleting remaining .asd files..."
echo "You may need to enter your password for sudo access."

# Count files first
COUNT=$(find /Volumes/MUSICALLY/[01]MUSIC-PROD:SRC/[01]Soundbank_DEER/02-Samples-Presets -name "*.asd" -type f | wc -l)
echo "Found $COUNT .asd files to delete"

# Delete with sudo
sudo find /Volumes/MUSICALLY/[01]MUSIC-PROD:SRC/[01]Soundbank_DEER/02-Samples-Presets -name "*.asd" -type f -delete

# Verify
REMAINING=$(find /Volumes/MUSICALLY/[01]MUSIC-PROD:SRC/[01]Soundbank_DEER/02-Samples-Presets -name "*.asd" -type f 2>/dev/null | wc -l)
echo "Deletion complete. Remaining .asd files: $REMAINING"