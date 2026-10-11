#!/bin/bash
cd "$(dirname "${BASH_SOURCE[0]}")"
PLUGINS_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Function to list VST3 plugins in a specified directory and save to file
list_vst3_plugins() {
    local directory=$1
    local output_file=$2

    if [ -d "$directory" ]; then
        echo "Listing VST3 plugins in $directory:" | tee -a "$output_file"
        ls "$directory" | tee -a "$output_file"
    else
        echo "Directory $directory does not exist." | tee -a "$output_file"
    fi
}

# New snapshot file only — does not overwrite plugins/installed_vst3_plugins.txt
output_file="$PLUGINS_ROOT/installed_vst3_plugins_live12.txt"
{
    echo "# Installed VST3 plugins — user + system macOS folders"
    echo "# Ableton Live 12 — $(date -u +"%Y-%m-%dT%H:%M:%SZ")"
    echo ""
} > "$output_file"

# List user-specific VST3 plugins
list_vst3_plugins ~/Library/Audio/Plug-Ins/VST3 "$output_file"

# List system-wide VST3 plugins
list_vst3_plugins /Library/Audio/Plug-Ins/VST3 "$output_file"

echo "The list of VST3 plugins has been printed to the terminal and saved to:"
echo "  $output_file"
