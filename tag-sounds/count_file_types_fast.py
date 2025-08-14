#!/usr/bin/env python3
"""
Fast file counter - counts files by extension without size calculation
"""

import os
from collections import Counter
from config import SAMPLES_PRESETS_PATH, OUTPUT_DIR

# Define file categories
FILE_CATEGORIES = {
    'Audio': {
        '.wav', '.mp3', '.aiff', '.aif', '.flac', '.ogg', '.m4a', 
        '.wma', '.aac', '.alac', '.ape', '.opus', '.dsd', '.dsf'
    },
    'Presets': {
        '.fxp', '.fxb', '.adg', '.adv', '.nmsv', '.patch', '.sxt', 
        '.vstpreset', '.aupreset', '.nksf', '.ksd', '.pst', '.fst',
        '.h2p', '.hip', '.sytrus', '.fsc', '.flp', '.als', '.alp',
        '.exs', '.nki', '.nkm', '.nkc', '.kmp', '.ens', '.isf'
    },
    'MIDI': {
        '.mid', '.midi', '.smf', '.kar', '.rmi'
    }
}

def quick_scan():
    """Quick scan - just count extensions"""
    extension_count = Counter()
    total_files = 0
    
    print(f"Fast scanning directory: {SAMPLES_PRESETS_PATH}")
    
    for root, dirs, files in os.walk(SAMPLES_PRESETS_PATH):
        for file in files:
            total_files += 1
            _, ext = os.path.splitext(file)
            if ext:
                extension_count[ext.lower()] += 1
            
            if total_files % 5000 == 0:
                print(f"  Processed {total_files:,} files...")
    
    # Categorize
    audio_count = 0
    preset_count = 0
    midi_count = 0
    other_count = 0
    
    for ext, count in extension_count.items():
        if ext in FILE_CATEGORIES['Audio']:
            audio_count += count
        elif ext in FILE_CATEGORIES['Presets']:
            preset_count += count
        elif ext in FILE_CATEGORIES['MIDI']:
            midi_count += count
        else:
            other_count += count
    
    print("\n" + "="*50)
    print("QUICK FILE COUNT RESULTS")
    print("="*50)
    print(f"\nTotal files: {total_files:,}")
    print(f"\nMain categories:")
    print(f"  Audio files:  {audio_count:,} ({audio_count/total_files*100:.1f}%)")
    print(f"  Preset files: {preset_count:,} ({preset_count/total_files*100:.1f}%)")
    print(f"  MIDI files:   {midi_count:,} ({midi_count/total_files*100:.1f}%)")
    print(f"  Other files:  {other_count:,} ({other_count/total_files*100:.1f}%)")
    
    print("\nTop 20 extensions:")
    for ext, count in extension_count.most_common(20):
        print(f"  {ext:10} {count:8,} files")
    
    # Save results
    with open(os.path.join(OUTPUT_DIR, 'quick_file_count.txt'), 'w') as f:
        f.write(f"Total files: {total_files:,}\n\n")
        f.write(f"Audio files:  {audio_count:,}\n")
        f.write(f"Preset files: {preset_count:,}\n")
        f.write(f"MIDI files:   {midi_count:,}\n")
        f.write(f"Other files:  {other_count:,}\n\n")
        f.write("All extensions:\n")
        for ext, count in sorted(extension_count.items()):
            f.write(f"  {ext}: {count:,}\n")

if __name__ == "__main__":
    quick_scan()