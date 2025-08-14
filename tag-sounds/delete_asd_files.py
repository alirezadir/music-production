#!/usr/bin/env python3
"""
Delete all .asd files from the samples directory
.asd files are Ableton's waveform cache files that can be regenerated
"""

import os
from config import SAMPLES_PRESETS_PATH

def delete_asd_files():
    """Find and delete all .asd files"""
    deleted_count = 0
    deleted_size = 0
    errors = []
    
    print(f"Scanning for .asd files in: {SAMPLES_PRESETS_PATH}")
    print("This will permanently delete all .asd files...")
    
    # First, count and show what will be deleted
    asd_files = []
    for root, dirs, files in os.walk(SAMPLES_PRESETS_PATH):
        for file in files:
            if file.lower().endswith('.asd'):
                filepath = os.path.join(root, file)
                try:
                    size = os.path.getsize(filepath)
                    asd_files.append((filepath, size))
                except:
                    pass
    
    if not asd_files:
        print("No .asd files found!")
        return
    
    total_size = sum(size for _, size in asd_files)
    print(f"\nFound {len(asd_files):,} .asd files")
    print(f"Total size: {total_size / (1024*1024):.2f} MB")
    
    # Show a few examples
    print("\nExample files to be deleted:")
    for filepath, _ in asd_files[:5]:
        rel_path = filepath.replace(SAMPLES_PRESETS_PATH, '')
        print(f"  {rel_path}")
    if len(asd_files) > 5:
        print(f"  ... and {len(asd_files) - 5:,} more files")
    
    # Confirm before deletion
    response = input("\nProceed with deletion? (yes/no): ")
    if response.lower() != 'yes':
        print("Deletion cancelled.")
        return
    
    # Delete files
    print("\nDeleting .asd files...")
    for filepath, size in asd_files:
        try:
            os.remove(filepath)
            deleted_count += 1
            deleted_size += size
            
            if deleted_count % 100 == 0:
                print(f"  Deleted {deleted_count:,} files...")
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
            print(f"  {filepath}: {error}")
        if len(errors) > 5:
            print(f"  ... and {len(errors) - 5} more errors")
    
    # Save report
    report_path = os.path.join(os.path.dirname(__file__), 'out', 'asd_deletion_report.txt')
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

if __name__ == "__main__":
    delete_asd_files()