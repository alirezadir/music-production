#!/usr/bin/env python3
"""
Unified file type counter - consolidates count_file_types and count_file_types_fast.

Counts files by extension with optional fast mode (no size calculation).
"""
import os
import argparse
from collections import defaultdict, Counter
from pathlib import Path
from typing import Dict, List, Tuple
import json
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from config import get_samples_path, get_tag_sounds_output_dir
    SAMPLES_PRESETS_PATH = get_samples_path().parent
    OUTPUT_DIR = get_tag_sounds_output_dir()
except ImportError:
    from config import SAMPLES_PRESETS_PATH, OUTPUT_DIR
    SAMPLES_PRESETS_PATH = Path(SAMPLES_PRESETS_PATH)
    OUTPUT_DIR = Path(OUTPUT_DIR)

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

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


def get_file_category(extension: str) -> str:
    """Determine which category a file belongs to based on its extension."""
    ext_lower = extension.lower()
    for category, extensions in FILE_CATEGORIES.items():
        if ext_lower in extensions:
            return category
    return 'Other'


def format_size(size_bytes: int) -> str:
    """Convert bytes to human readable format."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"


def scan_directory(base_path: Path, fast: bool = False) -> Dict:
    """Scan directory and count files by extension and category."""
    extension_count = Counter()
    category_count = defaultdict(int)
    category_details = defaultdict(lambda: defaultdict(int))
    total_files = 0
    total_size = 0
    
    # Track largest files (only in full mode)
    largest_files: List[Tuple[str, int]] = []
    
    print(f"Scanning directory: {base_path}")
    if fast:
        print("Fast mode: skipping size calculation...")
    else:
        print("Full mode: calculating file sizes...")
    
    try:
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
                    
                    # Get file size (only in full mode)
                    if not fast:
                        try:
                            size = os.path.getsize(filepath)
                            total_size += size
                            
                            # Track largest files
                            if len(largest_files) < 20 or size > largest_files[-1][1]:
                                largest_files.append((filepath.replace(str(base_path), ''), size))
                                largest_files.sort(key=lambda x: x[1], reverse=True)
                                largest_files = largest_files[:20]
                        except (OSError, PermissionError):
                            pass
                
                # Progress indicator
                if total_files % (5000 if fast else 1000) == 0:
                    print(f"  Processed {total_files:,} files...")
    except (PermissionError, FileNotFoundError) as e:
        print(f"Error scanning {base_path}: {e}")
        return {}
    
    return {
        'total_files': total_files,
        'total_size': total_size,
        'extension_count': dict(extension_count),
        'category_count': dict(category_count),
        'category_details': {k: dict(v) for k, v in category_details.items()},
        'largest_files': largest_files if not fast else []
    }


def generate_report(results: Dict, fast: bool = False, output_dir: Path = OUTPUT_DIR):
    """Generate and print detailed report."""
    print("\n" + "="*70)
    print("FILE TYPE ANALYSIS REPORT")
    print("="*70)
    
    print(f"\nTotal files scanned: {results['total_files']:,}")
    if not fast:
        print(f"Total size: {format_size(results['total_size'])}")
    
    # Category summary
    print("\n--- FILE CATEGORIES ---")
    category_count = results['category_count']
    sorted_categories = sorted(category_count.items(), key=lambda x: x[1], reverse=True)
    
    for category, count in sorted_categories:
        percentage = (count / results['total_files']) * 100 if results['total_files'] > 0 else 0
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
        percentage = (count / results['total_files']) * 100 if results['total_files'] > 0 else 0
        print(f"{ext:15} {count:8,} files ({percentage:5.1f}%)")
    
    # Largest files (only in full mode)
    if not fast and results['largest_files']:
        print("\n--- LARGEST FILES ---")
        for filepath, size in results['largest_files'][:10]:
            print(f"{format_size(size):>10}  {filepath}")
    
    # Save detailed results
    output_file = output_dir / ('file_type_analysis.json' if not fast else 'file_type_analysis_fast.json')
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nDetailed results saved to: {output_file}")
    
    # Create summary file
    summary_file = output_dir / ('file_type_summary.txt' if not fast else 'quick_file_count.txt')
    with open(summary_file, 'w') as f:
        f.write("FILE TYPE SUMMARY\n")
        f.write("=" * 50 + "\n\n")
        f.write(f"Total files: {results['total_files']:,}\n")
        if not fast:
            f.write(f"Total size: {format_size(results['total_size'])}\n\n")
        
        f.write("Main Categories:\n")
        for category, count in sorted_categories:
            percentage = (count / results['total_files']) * 100 if results['total_files'] > 0 else 0
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


def main():
    parser = argparse.ArgumentParser(
        description="Count files by extension and category"
    )
    parser.add_argument(
        '--fast',
        action='store_true',
        help='Fast mode: skip size calculation (faster)'
    )
    parser.add_argument(
        '--path',
        type=Path,
        help='Path to scan (overrides config)'
    )
    parser.add_argument(
        '--output',
        type=Path,
        help='Output directory (overrides config)'
    )
    
    args = parser.parse_args()
    
    # Determine base path
    if args.path:
        base_path = Path(args.path)
    else:
        base_path = Path(SAMPLES_PRESETS_PATH)
    
    if not base_path.exists():
        print(f"Error: Path does not exist: {base_path}")
        return 1
    
    # Determine output directory
    output_dir = Path(args.output) if args.output else OUTPUT_DIR
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Scan directory
    results = scan_directory(base_path, fast=args.fast)
    
    if not results:
        print("No results to report.")
        return 1
    
    # Generate report
    generate_report(results, fast=args.fast, output_dir=output_dir)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

