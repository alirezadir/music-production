#!/usr/bin/env python3
"""
Unified ASD file deleter - consolidates delete_asd_files and delete_asd_files_auto.

Deletes Ableton .asd waveform cache files with optional automatic mode.
"""
import os
import argparse
from pathlib import Path
from typing import List, Tuple
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from config import get_samples_path
    SAMPLES_PRESETS_PATH = get_samples_path().parent
except ImportError:
    from config import SAMPLES_PRESETS_PATH
    SAMPLES_PRESETS_PATH = Path(SAMPLES_PRESETS_PATH)


def delete_asd_files(auto: bool = False, base_path: Path = None) -> Tuple[int, int, List[Tuple[str, str]]]:
    """
    Find and delete all .asd files.
    
    Args:
        auto: If True, skip confirmation prompt
        base_path: Path to scan (defaults to config)
    
    Returns:
        Tuple of (deleted_count, deleted_size_bytes, errors)
    """
    if base_path is None:
        base_path = Path(SAMPLES_PRESETS_PATH)
    
    deleted_count = 0
    deleted_size = 0
    errors: List[Tuple[str, str]] = []
    
    print(f"Scanning for .asd files in: {base_path}")
    
    # First, find all .asd files
    asd_files: List[Tuple[str, int]] = []
    try:
        for root, dirs, files in os.walk(base_path):
            for file in files:
                if file.lower().endswith('.asd'):
                    filepath = os.path.join(root, file)
                    try:
                        size = os.path.getsize(filepath)
                        asd_files.append((filepath, size))
                    except (OSError, PermissionError):
                        pass
    except (PermissionError, FileNotFoundError) as e:
        print(f"Error scanning {base_path}: {e}")
        return 0, 0, [(str(base_path), str(e))]
    
    if not asd_files:
        print("No .asd files found!")
        return 0, 0, []
    
    total_size = sum(size for _, size in asd_files)
    print(f"\nFound {len(asd_files):,} .asd files")
    print(f"Total size: {total_size / (1024*1024):.2f} MB")
    
    # Show a few examples
    print("\nExample files to be deleted:")
    for filepath, _ in asd_files[:5]:
        rel_path = filepath.replace(str(base_path), '')
        print(f"  {rel_path}")
    if len(asd_files) > 5:
        print(f"  ... and {len(asd_files) - 5:,} more files")
    
    # Confirm before deletion (unless auto mode)
    if not auto:
        print("\nThese files are Ableton's waveform cache and will be regenerated when needed.")
        response = input("Proceed with deletion? (yes/no): ")
        if response.lower() != 'yes':
            print("Deletion cancelled.")
            return 0, 0, []
    else:
        print("\nAutomatic mode: proceeding with deletion...")
    
    # Delete files
    print("\nDeleting .asd files...")
    for filepath, size in asd_files:
        try:
            os.remove(filepath)
            deleted_count += 1
            deleted_size += size
            
            if deleted_count % (500 if auto else 100) == 0:
                print(f"  Deleted {deleted_count:,} files... ({deleted_size / (1024*1024):.1f} MB)")
        except Exception as e:
            errors.append((filepath, str(e)))
    
    # Report results
    print("\n" + "="*50)
    print("DELETION COMPLETE")
    print("="*50)
    print(f"Successfully deleted: {deleted_count:,} files")
    print(f"Space freed: {deleted_size / (1024*1024):.2f} MB")
    
    if errors:
        print(f"\nErrors encountered: {len(errors)}")
        for filepath, error in errors[:5]:
            rel_path = filepath.replace(str(base_path), '')
            print(f"  {rel_path}: {error}")
        if len(errors) > 5:
            print(f"  ... and {len(errors) - 5} more errors")
    
    # Save report
    output_dir = Path(__file__).parent / 'out'
    output_dir.mkdir(parents=True, exist_ok=True)
    report_path = output_dir / 'asd_deletion_report.txt'
    
    with open(report_path, 'w') as f:
        f.write(f"ASD File Deletion Report\n")
        f.write(f"========================\n\n")
        f.write(f"Files deleted: {deleted_count:,}\n")
        f.write(f"Space freed: {deleted_size / (1024*1024):.2f} MB\n")
        if errors:
            f.write(f"\nErrors:\n")
            for filepath, error in errors:
                f.write(f"  {filepath}: {error}\n")
    
    print(f"\nReport saved to: {report_path}")
    
    return deleted_count, deleted_size, errors


def main():
    parser = argparse.ArgumentParser(
        description="Delete Ableton .asd waveform cache files"
    )
    parser.add_argument(
        '--auto',
        action='store_true',
        help='Automatic mode: skip confirmation prompt'
    )
    parser.add_argument(
        '--path',
        type=Path,
        help='Path to scan (overrides config)'
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
    
    # Delete files
    deleted_count, deleted_size, errors = delete_asd_files(auto=args.auto, base_path=base_path)
    
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())

