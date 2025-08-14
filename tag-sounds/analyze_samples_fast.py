#!/usr/bin/env python3
import os
import re
from collections import defaultdict, Counter
import json
from config import SAMPLES_PRESETS_PATH, OUTPUT_DIR

# File paths for this script
OUTPUT_FILES = {
    'smart_analysis': f"{OUTPUT_DIR}/smart_analysis_results.json"
}

def extract_tokens_from_name(name):
    """Extract meaningful tokens from a filename or path"""
    # Remove file extension and convert to lowercase
    name = os.path.splitext(name)[0].lower()
    
    # Split by delimiters and clean
    tokens = re.split(r'[-_\s\.\(\)\[\]\/\\]+', name)
    
    # Filter tokens
    meaningful_tokens = []
    stop_words = {'the', 'and', 'vol', 'version', 'remix', 'edit', 'wav', 'audio', 
                  'sound', 'sample', 'pack', 'stereo', 'mono', 'dry', 'wet'}
    
    for token in tokens:
        if (len(token) > 2 and 
            not token.isdigit() and 
            token not in stop_words and
            not re.match(r'^\d+$', token) and
            not re.match(r'.*bpm.*', token) and
            not re.match(r'[a-g]#?(maj|min|m)$', token)):  # Skip musical keys
            meaningful_tokens.append(token)
    
    return meaningful_tokens

def main():
    print("Smart Sample Analysis - Fast Version")
    print("="*50)
    
    # Collect all tokens
    all_tokens = Counter()
    sample_count = 0
    
    print("Phase 1: Scanning files and extracting tokens...")
    
    for root, dirs, files in os.walk(SAMPLES_PRESETS_PATH):
        # Process wav files
        wav_files = [f for f in files if f.lower().endswith('.wav')]
        sample_count += len(wav_files)
        
        # Extract tokens from folder path
        folder_tokens = extract_tokens_from_name(root.replace(SAMPLES_PRESETS_PATH, ''))
        all_tokens.update(folder_tokens)
        
        # Sample some filenames (not all for speed)
        sample_files = wav_files[::max(1, len(wav_files)//50)]  # Sample every nth file
        for file in sample_files:
            file_tokens = extract_tokens_from_name(file)
            all_tokens.update(file_tokens)
    
    print(f"Found {sample_count:,} WAV files")
    print(f"Discovered {len(all_tokens):,} unique tokens")
    
    # Identify categories by frequency
    print("\nPhase 2: Identifying categories...")
    
    # Categories that appear frequently are likely meaningful
    frequent_tokens = {token: count for token, count in all_tokens.items() 
                      if count >= 5 and len(token) >= 3}
    
    # Separate sample types from shot types
    shot_keywords = {'loop', 'loops', 'oneshot', 'shot', 'hit', 'stab', 'phrase', 'pattern'}
    
    sample_categories = {}
    shot_categories = {}
    
    for token, count in frequent_tokens.items():
        if token in shot_keywords:
            shot_categories[token] = count
        else:
            sample_categories[token] = count
    
    # Sort by frequency
    sorted_sample_cats = sorted(sample_categories.items(), key=lambda x: x[1], reverse=True)
    sorted_shot_cats = sorted(shot_categories.items(), key=lambda x: x[1], reverse=True)
    
    print("\n--- TOP 30 SAMPLE CATEGORIES ---")
    for cat, count in sorted_sample_cats[:30]:
        print(f"{cat:20} {count:6} occurrences")
    
    print("\n--- SHOT CATEGORIES ---")
    for cat, count in sorted_shot_cats:
        print(f"{cat:20} {count:6} occurrences")
    
    print("\n--- ALL DISCOVERED TAGS (by frequency) ---")
    for token, count in sorted(frequent_tokens.items(), key=lambda x: x[1], reverse=True)[:50]:
        category_type = "SHOT" if token in shot_keywords else "SAMPLE"
        print(f"{token:20} {count:6} times [{category_type}]")
    
    # Save results
    results = {
        'total_wav_files': sample_count,
        'sample_categories': dict(sorted_sample_cats[:50]),
        'shot_categories': dict(sorted_shot_cats),
        'all_discovered_tags': dict(frequent_tokens),
        'analysis_method': 'fast_token_extraction'
    }
    
    # Ensure output directory exists
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    with open(OUTPUT_FILES['smart_analysis'], 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nResults saved to: {OUTPUT_FILES['smart_analysis']}")
    print(f"Total unique tags discovered: {len(frequent_tokens)}")

if __name__ == "__main__":
    main()