#!/usr/bin/env python3
import json
import os
from config import OUTPUT_DIR

# File paths for this script
INPUT_FILES = {
    'organized_tags': f"{OUTPUT_DIR}/organized_tags.json",
    'smart_analysis': f"{OUTPUT_DIR}/smart_analysis_results.json"
}

OUTPUT_FILES = {
    'sorted_tags': f"{OUTPUT_DIR}/sorted_tags.txt",
    'all_tags_list': f"{OUTPUT_DIR}/all_tags_list.txt",
    'tags_export': f"{OUTPUT_DIR}/tags_export.json"
}

def export_tags():
    # Ensure output directory exists
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Load the organized tags
    with open(INPUT_FILES['organized_tags'], 'r') as f:
        data = json.load(f)
    
    # Load the original data for all tags
    with open(INPUT_FILES['smart_analysis'], 'r') as f:
        original_data = json.load(f)
    
    # 1. Create sorted tags file with categories
    sorted_tags_content = "TAGS SORTED BY CATEGORY\n"
    sorted_tags_content += "="*50 + "\n\n"
    
    categorized = data['categorized_tags']
    
    # Sort categories for consistent output
    category_order = [
        'DRUM_TYPES', 'SHOT_TYPES', 'SYNTH_TYPES', 'VOCAL_TYPES', 
        'GENRES', 'PRODUCER_PACKS', 'PLUGINS', 'SOUND_CHARACTERISTICS',
        'MUSICAL_ELEMENTS', 'PACK_CODES', 'GENERIC_WORDS'
    ]
    
    for category in category_order:
        if category in categorized:
            sorted_tags_content += f"## {category.replace('_', ' ')}\n"
            # Sort by tag name
            sorted_items = sorted(categorized[category].items())
            for tag, count in sorted_items:
                sorted_tags_content += f"{tag}\n"
            sorted_tags_content += "\n"
    
    # Add uncategorized if any
    if data.get('uncategorized_tags'):
        sorted_tags_content += "## UNCATEGORIZED\n"
        for tag in sorted(data['uncategorized_tags'].keys()):
            sorted_tags_content += f"{tag}\n"
        sorted_tags_content += "\n"
    
    # Write sorted tags file
    with open(OUTPUT_FILES['sorted_tags'], 'w') as f:
        f.write(sorted_tags_content)
    
    # 2. Create all tags list (alphabetically sorted)
    all_tags = list(original_data['all_discovered_tags'].keys())
    all_tags.sort()
    
    all_tags_content = "ALL DISCOVERED TAGS (ALPHABETICAL)\n"
    all_tags_content += "="*50 + "\n\n"
    
    for tag in all_tags:
        all_tags_content += f"{tag}\n"
    
    # Write all tags file
    with open(OUTPUT_FILES['all_tags_list'], 'w') as f:
        f.write(all_tags_content)
    
    print("Files exported successfully!")
    print(f"1. {OUTPUT_FILES['sorted_tags']} - Tags organized by category")
    print(f"2. {OUTPUT_FILES['all_tags_list']} - All {len(all_tags)} tags in alphabetical order")
    
    # Also create a JSON version for easy programmatic access
    export_data = {
        'sorted_by_category': {cat: sorted(tags.keys()) for cat, tags in categorized.items()},
        'all_tags_alphabetical': all_tags,
        'total_tag_count': len(all_tags)
    }
    
    with open(OUTPUT_FILES['tags_export'], 'w') as f:
        json.dump(export_data, f, indent=2)
    
    print(f"3. {OUTPUT_FILES['tags_export']} - JSON format for programmatic use")

if __name__ == "__main__":
    export_tags()