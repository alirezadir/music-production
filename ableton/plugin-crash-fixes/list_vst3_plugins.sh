#!/bin/bash

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

# Output file to save the list of plugins
output_file="installed_vst3_plugins.txt"

# Clear the output file if it exists
> "$output_file"

# List user-specific VST3 plugins
list_vst3_plugins ~/Library/Audio/Plug-Ins/VST3 "$output_file"

# List system-wide VST3 plugins
list_vst3_plugins /Library/Audio/Plug-Ins/VST3 "$output_file"

echo "The list of VST3 plugins has been printed to the terminal and saved to $output_file."