#!/usr/bin/env python3
import json
import os
from collections import defaultdict
from config import OUTPUT_DIR

# File paths for this script
INPUT_FILES = {
    'smart_analysis': f"{OUTPUT_DIR}/smart_analysis_results.json"
}

OUTPUT_FILES = {
    'organized_tags': f"{OUTPUT_DIR}/organized_tags.json"
}

def categorize_tags():
    # Ensure output directory exists
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Load the analysis results
    with open(INPUT_FILES['smart_analysis'], 'r') as f:
        data = json.load(f)
    
    all_tags = data['all_discovered_tags']
    
    # Define tag categories
    tag_categories = {
        'DRUM_TYPES': [
            'kick', 'snare', 'clap', 'hihat', 'hat', 'tom', 'ride', 'crash', 
            'conga', 'shaker', 'drum', 'perc', 'percussion', 'percussive'
        ],
        'SHOT_TYPES': [
            'loop', 'loops', 'phrase', 'hit', 'shot', 'stab', 'oneshot', 'pattern'
        ],
        'SYNTH_TYPES': [
            'pad', 'lead', 'chord', 'bass', 'synth', 'synths', 'tonal'
        ],
        'VOCAL_TYPES': [
            'female', 'male', 'vocal', 'voc'
        ],
        'GENRES': [
            'techno', 'house', 'melodic', 'organic', 'deep'
        ],
        'PLUGINS': [
            'serum', 'diva', 'massive', 'ableton'
        ],
        'SOUND_CHARACTERISTICS': [
            'texture', 'dirty', 'long', 'short', 'foley', 'space', 'open', 
            'close', 'full', 'distortion'
        ],
        'MUSICAL_ELEMENTS': [
            'minor', 'chord', 'top', 'sounds', 'hits', 'kit'
        ],
        'PRODUCER_PACKS': [
            'pml', 'fvii', 'organica', 'boavista', 'elite', 'originals', 
            'market', 'lauren', 'laimant', 'ataraxia', 'collider'
        ],
        'PACK_CODES': [
            'dpv7', 'dpv8', 'veh1', 'veh2', 'vec1', 'vec2', 'pmlxsvt', 
            'pmlxsf', 'tsph', 'ztpt', 'ms20c', 'mth2', 'ztmot', 'tsfb', 
            'vp3', 'dje', 'ztnt', 'zttc', 'lvd', 'pmlxot3', 'omatic', 
            'sth', 'etct1', 'codacapca', 'weska2', 'ms37tsb'
        ],
        'GENERIC_WORDS': [
            'samples', 'presets', 'preset', 'packs', 'mix', 'you', 'like', 
            'nothing', 'project', 'vmh'
        ]
    }
    
    # Categorize all tags
    categorized_tags = defaultdict(list)
    uncategorized_tags = []
    
    for tag, count in all_tags.items():
        found_category = False
        for category, tag_list in tag_categories.items():
            if tag in tag_list:
                categorized_tags[category].append((tag, count))
                found_category = True
                break
        
        if not found_category:
            uncategorized_tags.append((tag, count))
    
    # Sort each category alphabetically by tag name
    for category in categorized_tags:
        categorized_tags[category].sort(key=lambda x: x[0])
    
    # Sort uncategorized tags alphabetically
    uncategorized_tags.sort(key=lambda x: x[0])
    
    # Print results
    print("TAGS ORGANIZED BY CATEGORY AND SORTED ALPHABETICALLY")
    print("="*60)
    
    for category, tags in sorted(categorized_tags.items()):
        print(f"\n--- {category.replace('_', ' ')} ---")
        for tag, count in tags:
            print(f"  {tag:20} ({count:,} occurrences)")
    
    if uncategorized_tags:
        print(f"\n--- UNCATEGORIZED TAGS ---")
        for tag, count in uncategorized_tags:
            print(f"  {tag:20} ({count:,} occurrences)")
    
    # Save organized results
    organized_results = {
        'categorized_tags': {k: dict(v) for k, v in categorized_tags.items()},
        'uncategorized_tags': dict(uncategorized_tags),
        'category_counts': {k: len(v) for k, v in categorized_tags.items()}
    }
    
    with open(OUTPUT_FILES['organized_tags'], 'w') as f:
        json.dump(organized_results, f, indent=2)
    
    print(f"\nResults saved to: {OUTPUT_FILES['organized_tags']}")
    
    # Print summary
    total_categorized = sum(len(tags) for tags in categorized_tags.values())
    total_uncategorized = len(uncategorized_tags)
    total_tags = total_categorized + total_uncategorized
    
    print(f"\nSUMMARY:")
    print(f"  Total tags: {total_tags}")
    print(f"  Categorized: {total_categorized}")
    print(f"  Uncategorized: {total_uncategorized}")
    print(f"  Categorization rate: {(total_categorized/total_tags)*100:.1f}%")

if __name__ == "__main__":
    categorize_tags()