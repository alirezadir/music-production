#!/bin/bash

# Function to remove all VST2 plugins from a specified directory
remove_all_vst2_plugins() {
    local directory=$1

    if [ -d "$directory" ]; then
        echo "Removing all VST2 plugins from $directory..."
        sudo rm -rf "$directory"/*
    else
        echo "Directory $directory does not exist."
    fi
}

# Remove all user-specific VST2 plugins
remove_all_vst2_plugins ~/Library/Audio/Plug-Ins/VST

# Remove all system-wide VST2 plugins
remove_all_vst2_plugins /Library/Audio/Plug-Ins/VST

echo "All VST2 plugins have been removed from the system."