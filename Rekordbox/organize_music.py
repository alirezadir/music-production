import os
import shutil
import hashlib
from datetime import datetime

def get_file_hash(file_path):
    """Compute the hash of a file."""
    hasher = hashlib.md5()
    with open(file_path, 'rb') as file:
        buffer = file.read()
        hasher.update(buffer)
    return hasher.hexdigest()

def organize_files_by_date(src_directory, dest_directory):
    """Organize files by their creation date, de-duplicate, and move them."""
    files_seen = {}
    for root, _, files in os.walk(src_directory):
        for file in files:
            if file.lower().endswith(('.mp3', '.wav', '.aiff')):
                file_path = os.path.join(root, file)
                file_hash = get_file_hash(file_path)

                # Check if this file is a duplicate
                if file_hash in files_seen:
                    print(f"Duplicate found: {file_path}")
                    continue
                else:
                    files_seen[file_hash] = file_path

                # Get the creation date of the file
                creation_date = datetime.fromtimestamp(os.path.getctime(file_path))
                year_month = creation_date.strftime('%Y/%m')

                # Create the destination directory if it doesn't exist
                destination_path = os.path.join(dest_directory, year_month)
                if not os.path.exists(destination_path):
                    os.makedirs(destination_path)

                # Move the file to the destination directory
                new_file_path = os.path.join(destination_path, file)
                shutil.move(file_path, new_file_path)
                print(f"Moved {file_path} to {new_file_path}")

# Example usage
src_directory = '/path/to/your/music/source'  # Replace with your source directory path
dest_directory = '/path/to/your/music/destination'  # Replace with your destination directory path

organize_files_by_date(src_directory, dest_directory)