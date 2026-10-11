#!/usr/bin/env python3
"""
Unified music file organizer - consolidates organize_music variants.

Organizes music files by creation date with deduplication support.
"""
import os
import shutil
import hashlib
import argparse
from datetime import datetime
from pathlib import Path
from typing import Optional
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from utils import get_file_hash, ensure_dir
except ImportError:
    # Fallback if utils not available
    def get_file_hash(file_path: Path) -> str:
        """Compute the hash of a file."""
        hasher = hashlib.md5()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hasher.update(chunk)
        return hasher.hexdigest()
    
    def ensure_dir(path: Path) -> Path:
        """Ensure a directory exists."""
        path = Path(path)
        path.mkdir(parents=True, exist_ok=True)
        return path


def organize_files_by_date(
    src_directory: Path,
    dest_directory: Path,
    deduplicate: bool = True,
    dry_run: bool = False
) -> dict:
    """
    Organize files by their creation date, de-duplicate, and move them.
    
    Args:
        src_directory: Source directory to scan
        dest_directory: Destination directory for organized files
        deduplicate: If True, skip duplicate files (by hash)
        dry_run: If True, don't actually move files, just report
    
    Returns:
        Dictionary with statistics
    """
    files_seen = {}
    stats = {
        'total_found': 0,
        'moved': 0,
        'duplicates_skipped': 0,
        'errors': 0,
        'errors_list': []
    }
    
    # Supported audio file extensions
    audio_extensions = {'.mp3', '.wav', '.aiff', '.aif', '.flac', '.m4a', '.ogg'}
    
    print(f"Scanning source directory: {src_directory}")
    print(f"Destination directory: {dest_directory}")
    if deduplicate:
        print("Deduplication: ENABLED")
    if dry_run:
        print("DRY RUN MODE: No files will be moved")
    print()
    
    try:
        for root, dirs, files in os.walk(src_directory):
            for file in files:
                file_path = Path(root) / file
                
                # Check if it's an audio file
                if file_path.suffix.lower() not in audio_extensions:
                    continue
                
                stats['total_found'] += 1
                
                # Deduplication check
                if deduplicate:
                    try:
                        file_hash = get_file_hash(file_path)
                        
                        # Check if this file is a duplicate
                        if file_hash in files_seen:
                            stats['duplicates_skipped'] += 1
                            if stats['duplicates_skipped'] <= 5:
                                print(f"Duplicate found: {file_path}")
                            continue
                        else:
                            files_seen[file_hash] = file_path
                    except Exception as e:
                        stats['errors'] += 1
                        stats['errors_list'].append(f"Hash error for {file_path}: {e}")
                        continue
                
                # Get the creation date of the file
                try:
                    creation_date = datetime.fromtimestamp(os.path.getctime(file_path))
                    year_month = creation_date.strftime('%Y/%m')
                except OSError as e:
                    stats['errors'] += 1
                    stats['errors_list'].append(f"Date error for {file_path}: {e}")
                    continue
                
                # Create the destination directory
                destination_path = ensure_dir(dest_directory / year_month)
                
                # Move the file
                new_file_path = destination_path / file.name
                
                # Handle name conflicts
                counter = 1
                while new_file_path.exists():
                    stem = file_path.stem
                    suffix = file_path.suffix
                    new_file_path = destination_path / f"{stem}_{counter}{suffix}"
                    counter += 1
                
                if not dry_run:
                    try:
                        shutil.move(str(file_path), str(new_file_path))
                        stats['moved'] += 1
                        if stats['moved'] % 100 == 0:
                            print(f"  Moved {stats['moved']:,} files...")
                    except Exception as e:
                        stats['errors'] += 1
                        stats['errors_list'].append(f"Move error for {file_path}: {e}")
                else:
                    stats['moved'] += 1
                    if stats['moved'] <= 10:
                        print(f"Would move: {file_path} -> {new_file_path}")
                
    except Exception as e:
        print(f"Error during organization: {e}")
        stats['errors'] += 1
        stats['errors_list'].append(f"General error: {e}")
    
    return stats


def main():
    parser = argparse.ArgumentParser(
        description="Organize music files by creation date with deduplication"
    )
    parser.add_argument(
        '--source',
        type=Path,
        required=True,
        help='Source directory to scan'
    )
    parser.add_argument(
        '--dest',
        type=Path,
        required=True,
        help='Destination directory for organized files'
    )
    parser.add_argument(
        '--no-dedup',
        action='store_true',
        help='Disable deduplication'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Dry run: show what would be done without actually moving files'
    )
    
    args = parser.parse_args()
    
    # Validate paths
    if not args.source.exists():
        print(f"Error: Source directory does not exist: {args.source}")
        return 1
    
    if not args.source.is_dir():
        print(f"Error: Source path is not a directory: {args.source}")
        return 1
    
    # Run organization
    stats = organize_files_by_date(
        args.source,
        args.dest,
        deduplicate=not args.no_dedup,
        dry_run=args.dry_run
    )
    
    # Print summary
    print("\n" + "="*50)
    print("ORGANIZATION COMPLETE")
    print("="*50)
    print(f"Total files found: {stats['total_found']:,}")
    print(f"Files moved: {stats['moved']:,}")
    if stats['duplicates_skipped'] > 0:
        print(f"Duplicates skipped: {stats['duplicates_skipped']:,}")
    if stats['errors'] > 0:
        print(f"Errors: {stats['errors']}")
        if stats['errors_list']:
            print("\nFirst few errors:")
            for error in stats['errors_list'][:5]:
                print(f"  {error}")
    
    return 0 if stats['errors'] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

