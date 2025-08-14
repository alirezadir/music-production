#!/bin/bash

# Create output directory with date only
OUTPUT_DIR="./Plugin_Export_$(date +%Y%m%d)"
mkdir -p "$OUTPUT_DIR"

echo "🔍 Scanning plugins..."

# Create temp file
TEMP_FILE="$OUTPUT_DIR/temp_plugins.txt"
> "$TEMP_FILE"

# Function to collect plugins
collect_plugins() {
    local path="$1"
    local extension="$2"
    local format="$3"
    
    if [ -d "$path" ]; then
        find "$path" -maxdepth 1 -name "*.$extension" 2>/dev/null | while read -r plugin; do
            name=$(basename "$plugin" ".$extension")
            echo "${name}|${format}" >> "$TEMP_FILE"
        done
    fi
}

# Collect all plugins
collect_plugins "/Library/Audio/Plug-Ins/Components" "component" "AU"
collect_plugins "$HOME/Library/Audio/Plug-Ins/Components" "component" "AU"
collect_plugins "/Library/Audio/Plug-Ins/VST" "vst" "VST2"
collect_plugins "$HOME/Library/Audio/Plug-Ins/VST" "vst" "VST2"
collect_plugins "/Library/Audio/Plug-Ins/VST3" "vst3" "VST3"
collect_plugins "$HOME/Library/Audio/Plug-Ins/VST3" "vst3" "VST3"

# Create AU plugins file
{
    au_count=$(grep "|AU$" "$TEMP_FILE" | cut -d'|' -f1 | sort -u | wc -l)
    echo "Total AU plugins: $au_count"
    echo "-----------------------"
    grep "|AU$" "$TEMP_FILE" | cut -d'|' -f1 | sort -u
} > "$OUTPUT_DIR/AU_plugins.txt"

# Create VST2 plugins file
{
    vst2_count=$(grep "|VST2$" "$TEMP_FILE" | cut -d'|' -f1 | sort -u | wc -l)
    echo "Total VST2 plugins: $vst2_count"
    echo "-----------------------"
    grep "|VST2$" "$TEMP_FILE" | cut -d'|' -f1 | sort -u
} > "$OUTPUT_DIR/VST2_plugins.txt"

# Create VST3 plugins file
{
    vst3_count=$(grep "|VST3$" "$TEMP_FILE" | cut -d'|' -f1 | sort -u | wc -l)
    echo "Total VST3 plugins: $vst3_count"
    echo "-----------------------"
    grep "|VST3$" "$TEMP_FILE" | cut -d'|' -f1 | sort -u
} > "$OUTPUT_DIR/VST3_plugins.txt"

# Create combined summary
{
    unique_count=$(cut -d'|' -f1 "$TEMP_FILE" | sort -u | wc -l)
    echo "Total unique plugins: $unique_count"
    echo "-----------------------"
    
    cut -d'|' -f1 "$TEMP_FILE" | sort -u | while read -r plugin_name; do
        if [ -n "$plugin_name" ]; then
            formats=$(grep "^${plugin_name}|" "$TEMP_FILE" | cut -d'|' -f2 | sort -u | tr '\n' ', ' | sed 's/, $//')
            echo "$plugin_name ($formats)"
        fi
    done
} > "$OUTPUT_DIR/all_plugins.txt"

# Clean up
rm -f "$TEMP_FILE"

# Display summary
echo ""
echo "✅ Export complete!"
echo ""
echo "📊 Summary:"
echo "-----------"
echo "AU plugins:   $(grep "Total AU plugins:" "$OUTPUT_DIR/AU_plugins.txt" | cut -d: -f2)"
echo "VST2 plugins: $(grep "Total VST2 plugins:" "$OUTPUT_DIR/VST2_plugins.txt" | cut -d: -f2)"
echo "VST3 plugins: $(grep "Total VST3 plugins:" "$OUTPUT_DIR/VST3_plugins.txt" | cut -d: -f2)"
echo "Unique total: $(grep "Total unique plugins:" "$OUTPUT_DIR/all_plugins.txt" | cut -d: -f2)"
echo ""
echo "📁 Files saved in: $OUTPUT_DIR/"
echo "- all_plugins.txt  (combined list)"
echo "- AU_plugins.txt   (Audio Units only)"
echo "- VST2_plugins.txt (VST2 only)"
echo "- VST3_plugins.txt (VST3 only)"