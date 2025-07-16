#!/bin/bash

# Create directories for backups
backup_dir=~/Workspace/AIG/ableton/plugin_backup
mkdir -p "$backup_dir/VST"
mkdir -p "$backup_dir/VST3"
mkdir -p "$backup_dir/AU"

# List VST plugins and save to a text file
echo "Listing VST plugins..."
vst_list="$backup_dir/Installed_VST_Plugins.txt"
ls /Library/Audio/Plug-Ins/VST/ > "$vst_list"
ls ~/Library/Audio/Plug-Ins/VST/ >> "$vst_list"

# Backup VST plugin directory
echo "Backing up VST plugins..."
cp -r /Library/Audio/Plug-Ins/VST/ "$backup_dir/VST/"
cp -r ~/Library/Audio/Plug-Ins/VST/ "$backup_dir/VST/"

# List VST3 plugins and save to a text file
echo "Listing VST3 plugins..."
vst3_list="$backup_dir/Installed_VST3_Plugins.txt"
ls /Library/Audio/Plug-Ins/VST3/ > "$vst3_list"
ls ~/Library/Audio/Plug-Ins/VST3/ >> "$vst3_list"

# Backup VST3 plugin directory
echo "Backing up VST3 plugins..."
cp -r /Library/Audio/Plug-Ins/VST3/ "$backup_dir/VST3/"
cp -r ~/Library/Audio/Plug-Ins/VST3/ "$backup_dir/VST3/"

# List AU plugins and save to a text file
echo "Listing AU plugins..."
au_list="$backup_dir/Installed_AU_Plugins.txt"
ls /Library/Audio/Plug-Ins/Components/ > "$au_list"
ls ~/Library/Audio/Plug-Ins/Components/ >> "$au_list"

# Backup AU plugin directory
echo "Backing up AU plugins..."
cp -r /Library/Audio/Plug-Ins/Components/ "$backup_dir/AU/"
cp -r ~/Library/Audio/Plug-Ins/Components/ "$backup_dir/AU/"

echo "Plugin listing and backup completed. Files are saved in $backup_dir"