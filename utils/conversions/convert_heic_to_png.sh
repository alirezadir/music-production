# #!/bin/bash

# # Check if the directory argument is provided
# if [ -z "$1" ]; then
#     echo "Please provide the directory containing the .HEIC files as an argument."
#     exit 1
# fi

# # Directory containing the .HEIC files
# DIRECTORY="$1"

# # Loop through all .HEIC files in the directory
# for file in "$DIRECTORY"/*.HEIC; do
#     # Check if there are no .HEIC files
#     if [ ! -e "$file" ]; then
#         echo "No .HEIC files found in the directory."
#         exit 1
#     fi

#     # Get the base name of the file (without extension)
#     base_name=$(basename "$file" .HEIC)
    
#     # Convert HEIC to PNG using ffmpeg while preserving color and selecting the correct stream
#     ffmpeg -i "$file" -map 0:v:0 -vf "format=rgb24" "$DIRECTORY/$base_name.png"
    
#     # Check if the PNG file was created successfully
#     if [ -f "$DIRECTORY/$base_name.png" ]; then
#         # Delete the original HEIC file
#         rm "$file"
#         echo "Converted and deleted: $file"
#     else
#         echo "Failed to convert: $file"
#     fi
# done

#!/bin/bash

# Check if the directory argument is provided
if [ -z "$1" ]; then
    echo "Please provide the directory containing the .HEIC files as an argument."
    exit 1
fi

# Directory containing the .HEIC files
DIRECTORY="$1"

# Loop through all .HEIC files in the directory
for file in "$DIRECTORY"/*.HEIC; do
    # Check if there are no .HEIC files
    if [ ! -e "$file" ]; then
        echo "No .HEIC files found in the directory."
        exit 1
    fi

    # Get the base name of the file (without extension)
    base_name=$(basename "$file" .HEIC)
    
    # Convert HEIC to PNG
    heif-convert "$file" "$DIRECTORY/$base_name.png"
    
    # Check if the PNG file was created successfully
    if [ -f "$DIRECTORY/$base_name.png" ]; then
        # Delete the original HEIC file
        rm "$file"
        echo "Converted and deleted: $file"
    else
        echo "Failed to convert: $file"
    fi
done