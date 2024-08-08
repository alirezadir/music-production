#!/bin/bash

# Remove Analog Lab V
echo "Removing Analog Lab V..."
sudo rm -rf /Library/Audio/Plug-Ins/VST/Analog\ Lab\ V.vst
sudo rm -rf /Library/Audio/Plug-Ins/VST3/Analog\ Lab\ V.vst3
sudo rm -rf /Library/Audio/Plug-Ins/Components/Analog\ Lab\ V.component
rm -rf ~/Library/Audio/Plug-Ins/VST/Analog\ Lab\ V.vst
rm -rf ~/Library/Audio/Plug-Ins/VST3/Analog\ Lab\ V.vst3
rm -rf ~/Library/Audio/Plug-Ins/Components/Analog\ Lab\ V.component
rm -rf ~/Library/Arturia/Analog\ Lab\ V/
rm -rf ~/Library/Preferences/com.arturia.AnalogLabV.plist

# Remove Nectar 3
echo "Removing Nectar 3..."
sudo rm -rf /Library/Audio/Plug-Ins/VST/iZotope\ Nectar\ 3.vst
sudo rm -rf /Library/Audio/Plug-Ins/VST3/iZotope\ Nectar\ 3.vst3
sudo rm -rf /Library/Audio/Plug-Ins/Components/iZotope\ Nectar\ 3.component
sudo rm -rf /Library/Application\ Support/Avid/Audio/Plug-Ins/iZotope\ Nectar\ 3.aaxplugin
rm -rf ~/Library/Audio/Plug-Ins/VST/iZotope\ Nectar\ 3.vst
rm -rf ~/Library/Audio/Plug-Ins/VST3/iZotope\ Nectar\ 3.vst3
rm -rf ~/Library/Audio/Plug-Ins/Components/iZotope\ Nectar\ 3.component
rm -rf ~/Documents/iZotope/Nectar\ 3/
rm -rf ~/Library/Preferences/com.izotope.audioplugins.Nectar3.plist

# Remove Kilohearts (kHs)
echo "Removing Kilohearts (kHs)..."
sudo rm -rf /Library/Audio/Plug-Ins/VST/kHs
sudo rm -rf /Library/Audio/Plug-Ins/VST3/kHs
sudo rm -rf /Library/Audio/Plug-Ins/Components/kHs
sudo rm -rf /Library/Application\ Support/Avid/Audio/Plug-Ins/kHs
rm -rf ~/Library/Audio/Plug-Ins/VST/kHs
rm -rf ~/Library/Audio/Plug-Ins/VST3/kHs
rm -rf ~/Library/Audio/Plug-Ins/Components/kHs
rm -rf ~/Documents/Kilohearts/
rm -rf ~/Library/Preferences/com.kilohearts.*


#!/bin/bash

# Remove EastWest Opus VST2 Plugin
echo "Removing EastWest Opus VST2 Plugin..."
sudo rm -rf /Library/Audio/Plug-Ins/VST/EastWest/Opus.vst
rm -rf ~/Library/Audio/Plug-Ins/VST/EastWest/Opus.vst

# Remove EastWest Opus VST3 Plugin
echo "Removing EastWest Opus VST3 Plugin..."
sudo rm -rf /Library/Audio/Plug-Ins/VST3/EastWest/Opus.vst3
rm -rf ~/Library/Audio/Plug-Ins/VST3/EastWest/Opus.vst3

# Remove EastWest Opus AU Plugin
echo "Removing EastWest Opus AU Plugin..."
sudo rm -rf /Library/Audio/Plug-Ins/Components/Opus.component
rm -rf ~/Library/Audio/Plug-Ins/Components/Opus.component

# Remove EastWest Opus AAX Plugin
echo "Removing EastWest Opus AAX Plugin..."
sudo rm -rf /Library/Application\ Support/Avid/Audio/Plug-Ins/Opus.aaxplugin

# Remove EastWest Opus Presets and Settings
echo "Removing EastWest Opus Presets and Settings..."
rm -rf ~/Documents/EastWest/Opus

# Remove EastWest Opus Preferences
echo "Removing EastWest Opus Preferences..."
rm -rf ~/Library/Preferences/com.soundsonline.Opus.plist

echo "EastWest Opus plugin and its associated files have been removed."


#!/bin/bash

# Remove Waves 14 VST2 Plugins
echo "Removing Waves 14 VST2 Plugins..."
sudo rm -rf /Library/Audio/Plug-Ins/VST/Waves
rm -rf ~/Library/Audio/Plug-Ins/VST/Waves

# Remove Waves 14 VST3 Plugins
echo "Removing Waves 14 VST3 Plugins..."
sudo rm -rf /Library/Audio/Plug-Ins/VST3/Waves
rm -rf ~/Library/Audio/Plug-Ins/VST3/Waves

# Remove Waves 14 AU Plugins
echo "Removing Waves 14 AU Plugins..."
sudo rm -rf /Library/Audio/Plug-Ins/Components/Waves.component
rm -rf ~/Library/Audio/Plug-Ins/Components/Waves.component

# Remove Waves 14 AAX Plugins
echo "Removing Waves 14 AAX Plugins..."
sudo rm -rf /Library/Application\ Support/Avid/Audio/Plug-Ins/Waves

# Remove Waves 14 Applications
echo "Removing Waves 14 Applications..."
sudo rm -rf /Applications/Waves

# Remove Waves 14 Presets and Settings
echo "Removing Waves 14 Presets and Settings..."
rm -rf ~/Library/Application\ Support/Waves\ Audio
rm -rf ~/Documents/Waves\ Audio

# Remove Waves 14 Preferences
echo "Removing Waves 14 Preferences..."
rm -rf ~/Library/Preferences/com.wavesaudio.*

# Remove Waves 14 Caches
echo "Removing Waves 14 Caches..."
rm -rf ~/Library/Caches/Waves\ Audio

echo "Waves 14 plugins and their associated files have been removed."


echo "All specified plugins have been removed."