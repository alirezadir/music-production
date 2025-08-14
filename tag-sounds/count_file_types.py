#!/usr/bin/env python3
"""
Count files by extension in the 02-Samples-Presets directory
Groups files into categories: Audio, Presets, MIDI, and Other
"""

import os
from collections import defaultdict, Counter
import json
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
    },
    'Project Files': {
        '.als', '.alc', '.flp', '.logic', '.ptx', '.cpr', '.cwp',
        '.rpp', '.band', '.sesx', '.omg', '.omf', '.npr'
    },
    'Archive': {
        '.zip', '.rar', '.7z', '.tar', '.gz', '.bz2', '.xz'
    },
    'Documents': {
        '.pdf', '.txt', '.doc', '.docx', '.rtf', '.md', '.nfo'
    },
    'Images': {
        '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.svg',
        '.ico', '.webp'
    }
}

def get_file_category(extension):
    """Determine which category a file belongs to based on its extension"""
    ext_lower = extension.lower()
    for category, extensions in FILE_CATEGORIES.items():
        if ext_lower in extensions:
            return category
    return 'Other'

def scan_directory(base_path):
    """Scan directory and count files by extension and category"""
    extension_count = Counter()
    category_count = defaultdict(int)
    category_details = defaultdict(lambda: defaultdict(int))
    total_files = 0
    total_size = 0
    
    # Track largest files
    largest_files = []
    
    print(f"Scanning directory: {base_path}")
    print("This may take a moment...")
    
    for root, dirs, files in os.walk(base_path):
        for file in files:
            total_files += 1
            filepath = os.path.join(root, file)
            
            # Get file extension
            _, ext = os.path.splitext(file)
            if ext:  # Only count files with extensions
                extension_count[ext.lower()] += 1
                
                # Get category
                category = get_file_category(ext)
                category_count[category] += 1
                category_details[category][ext.lower()] += 1
                
                # Get file size
                try:
                    size = os.path.getsize(filepath)
                    total_size += size
                    
                    # Track largest files
                    if len(largest_files) < 20 or size > largest_files[-1][1]:
                        largest_files.append((filepath.replace(base_path, ''), size))
                        largest_files.sort(key=lambda x: x[1], reverse=True)
                        largest_files = largest_files[:20]
                except:
                    pass
            
            # Progress indicator
            if total_files % 1000 == 0:
                print(f"  Processed {total_files:,} files...")
    
    return {
        'total_files': total_files,
        'total_size': total_size,
        'extension_count': dict(extension_count),
        'category_count': dict(category_count),
        'category_details': {k: dict(v) for k, v in category_details.items()},
        'largest_files': largest_files
    }

def format_size(size_bytes):
    """Convert bytes to human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"

def generate_report(results):
    """Generate and print detailed report"""
    print("\n" + "="*70)
    print("FILE TYPE ANALYSIS REPORT")
    print("="*70)
    
    print(f"\nTotal files scanned: {results['total_files']:,}")
    print(f"Total size: {format_size(results['total_size'])}")
    
    # Category summary
    print("\n--- FILE CATEGORIES ---")
    category_count = results['category_count']
    sorted_categories = sorted(category_count.items(), key=lambda x: x[1], reverse=True)
    
    for category, count in sorted_categories:
        percentage = (count / results['total_files']) * 100
        print(f"{category:20} {count:8,} files ({percentage:5.1f}%)")
    
    # Detailed breakdown by category
    print("\n--- DETAILED BREAKDOWN BY CATEGORY ---")
    for category in ['Audio', 'Presets', 'MIDI', 'Project Files']:
        if category in results['category_details']:
            print(f"\n{category}:")
            details = results['category_details'][category]
            sorted_exts = sorted(details.items(), key=lambda x: x[1], reverse=True)
            for ext, count in sorted_exts[:10]:  # Top 10 extensions per category
                print(f"  {ext:15} {count:8,} files")
    
    # Top extensions overall
    print("\n--- TOP 20 FILE EXTENSIONS ---")
    sorted_extensions = sorted(results['extension_count'].items(), 
                             key=lambda x: x[1], reverse=True)
    for ext, count in sorted_extensions[:20]:
        percentage = (count / results['total_files']) * 100
        print(f"{ext:15} {count:8,} files ({percentage:5.1f}%)")
    
    # Largest files
    print("\n--- LARGEST FILES ---")
    for filepath, size in results['largest_files'][:10]:
        print(f"{format_size(size):>10}  {filepath}")
    
    # Save detailed results
    output_file = os.path.join(OUTPUT_DIR, 'file_type_analysis.json')
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nDetailed results saved to: {output_file}")
    
    # Create summary file
    summary_file = os.path.join(OUTPUT_DIR, 'file_type_summary.txt')
    with open(summary_file, 'w') as f:
        f.write("FILE TYPE SUMMARY\n")
        f.write("=" * 50 + "\n\n")
        f.write(f"Total files: {results['total_files']:,}\n")
        f.write(f"Total size: {format_size(results['total_size'])}\n\n")
        
        f.write("Main Categories:\n")
        for category, count in sorted_categories:
            percentage = (count / results['total_files']) * 100
            f.write(f"  {category:20} {count:8,} files ({percentage:5.1f}%)\n")
        
        f.write("\n\nAudio Files:\n")
        if 'Audio' in results['category_details']:
            audio_total = sum(results['category_details']['Audio'].values())
            f.write(f"  Total: {audio_total:,} files\n")
            for ext, count in sorted(results['category_details']['Audio'].items(), 
                                    key=lambda x: x[1], reverse=True):
                f.write(f"    {ext}: {count:,}\n")
        
        f.write("\n\nPreset Files:\n")
        if 'Presets' in results['category_details']:
            preset_total = sum(results['category_details']['Presets'].values())
            f.write(f"  Total: {preset_total:,} files\n")
            for ext, count in sorted(results['category_details']['Presets'].items(), 
                                    key=lambda x: x[1], reverse=True):
                f.write(f"    {ext}: {count:,}\n")
        
        f.write("\n\nMIDI Files:\n")
        if 'MIDI' in results['category_details']:
            midi_total = sum(results['category_details']['MIDI'].values())
            f.write(f"  Total: {midi_total:,} files\n")
            for ext, count in sorted(results['category_details']['MIDI'].items(), 
                                    key=lambda x: x[1], reverse=True):
                f.write(f"    {ext}: {count:,}\n")
    
    print(f"Summary saved to: {summary_file}")

if __name__ == "__main__":
    results = scan_directory(SAMPLES_PRESETS_PATH)
    generate_report(results)