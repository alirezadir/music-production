#!/bin/bash

# Function to confirm and remove plugins from a specified directory
remove_vst3_plugins() {
    local directory=$1

    if [ -d "$directory" ]; then
        echo "Removing all VST3 plugins from $directory..."
        sudo rm -rf "$directory"/*
    else
        echo "Directory $directory does not exist."
    fi
}

# Remove system-wide VST3 plugins
remove_vst3_plugins /Library/Audio/Plug-Ins/VST3

# Remove user-specific VST3 plugins
remove_vst3_plugins ~/Library/Audio/Plug-Ins/VST3

echo "All user-installed VST3 plugins have been removed from the system."