#!/bin/bash

# Replace x.x.x with your Ableton Live version
ABLETON_VERSION="Live x.x.x"

echo "Deleting Ableton Live preferences..."
rm -rf ~/Library/Preferences/Ableton/"$ABLETON_VERSION"/

echo "Deleting Ableton Live PluginScanInfo..."
rm -rf ~/Library/Preferences/Ableton/"$ABLETON_VERSION"/PluginScanInfo

echo "Deleting Ableton Live Cache..."
rm -rf ~/Library/Preferences/Ableton/"$ABLETON_VERSION"/Cache

echo "Deleting Melodyne files..."
sudo rm -rf /Library/Audio/Plug-Ins/VST/Melodyne.vst
sudo rm -rf /Library/Audio/Plug-Ins/VST3/Melodyne.vst3
sudo rm -rf /Library/Audio/Plug-Ins/Components/Melodyne.component
sudo rm -rf /Library/Application\ Support/Avid/Audio/Plug-Ins/Melodyne.aaxplugin
sudo rm -rf /Library/Application\ Support/Celemony
sudo rm -rf ~/Library/Application\ Support/Celemony
sudo rm -rf ~/Library/Preferences/com.celemony.Melodyne.plist

echo "Deleting Kilohearts (KHS) plugins..."
sudo rm -rf /Library/Audio/Plug-Ins/VST/Kilohearts
sudo rm -rf /Library/Audio/Plug-Ins/VST3/Kilohearts
sudo rm -rf /Library/Audio/Plug-Ins/Components/Kilohearts.component
sudo rm -rf /Library/Application\ Support/Avid/Audio/Plug-Ins/Kilohearts.aaxplugin
sudo rm -rf /Library/Application\ Support/Kilohearts
sudo rm -rf ~/Library/Application\ Support/Kilohearts
sudo rm -rf ~/Library/Preferences/com.kilohearts.*

echo "Ableton Live crash fix process completed. Please restart Ableton Live and try again."
echo "If issues persist, consider reinstalling Ableton Live and updating all plugins."
