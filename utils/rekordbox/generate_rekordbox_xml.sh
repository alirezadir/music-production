#!/bin/bash

# Define source and destination directories
SRC_DIR="/Users/alirezadirafzoon/Music/Beats"  
DEST_DIR="/Users/alirezadirafzoon/Music/DJLib"  

# Create XML header
echo '<?xml version="1.0" encoding="UTF-8"?>' > rekordbox.xml
echo '<DJ_PLAYLISTS Version="1.0.0">' >> rekordbox.xml
echo '  <COLLECTION>' >> rekordbox.xml

# Find all music files and generate XML entries
find "$DEST_DIR" -type f \( -iname "*.mp3" -o -iname "*.wav" -o -iname "*.aiff" \) | while read -r file; do
    track_name=$(basename "$file")
    track_path=$(dirname "$file")
    track_path="${track_path/$DEST_DIR\/}"

    echo "  <TRACK Name=\"$track_name\" Location=\"file://localhost/$track_path/$track_name\" />" >> rekordbox.xml
done

# Close XML tags
echo '  </COLLECTION>' >> rekordbox.xml
echo '</DJ_PLAYLISTS>' >> rekordbox.xml