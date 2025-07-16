#!/bin/bash

# Paths to scan for Ableton instruments and plugins
ABLETON_USER_LIBRARY="$HOME/Music/Ableton/User Library"
PLUGINS_PATHS=(
    "$HOME/Library/Audio/Plug-Ins/VST"
    "$HOME/Library/Audio/Plug-Ins/VST3"
    "$HOME/Library/Audio/Plug-Ins/Components"  # AU Plugins
)

# Function to list Ableton instruments
list_instruments() {
    echo "Scanning Ableton User Library for instruments..."
    find "$ABLETON_USER_LIBRARY" -type f \( -name "*.adv" -o -name "*.adg" \) 2>/dev/null | while read -r file; do
        basename "$file"
    done

    echo ""
    echo "Scanning plugin folders for VST, VST3, and AU instruments..."
    for plugin_path in "${PLUGINS_PATHS[@]}"; do
        if [ -d "$plugin_path" ]; then
            find "$plugin_path" -type f \( -name "*.vst" -o -name "*.vst3" -o -name "*.component" \) 2>/dev/null | while read -r file; do
                basename "$file"
            done
        fi
    done
}

# Run the function and output results
echo "Installed Ableton Instruments:"
list_instruments | sort | uniq