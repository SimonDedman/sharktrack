#!/bin/bash

# Script to process BRUV MP4 files
set -e

SOURCE_DIR="/home/simon/Documents/Si Work/PostDoc Work/Saving The Blue/Data/BRUV"
WORK_DIR="/tmp/bruvdata"

# Create working directory
mkdir -p "$WORK_DIR"

# Find all MP4 files in source directory
find "$SOURCE_DIR" -name "*.MP4" -o -name "*.mp4" | while read -r file; do
    # Extract filename without path
    filename=$(basename "$file")
    # Extract name without extension
    name="${filename%.*}"

    echo "Processing $filename..."

    # Create directory for this file
    file_dir="$WORK_DIR/$name"
    mkdir -p "$file_dir"

    # Create hardlink (note: using ln without -s for hardlink, not symlink)
    ln "$file" "$file_dir/$filename"

    # Run reformatting script
    echo "Running reformat for $name..."
    python utils/reformat_gopro.py --input "$file_dir" --output "$file_dir/reformat"

    # Run main processing
    echo "Running app.py for $name..."
    python app.py --input "$file_dir/reformat" --output "$file_dir/output"

    echo "Completed processing $filename"
    echo "---"
done

echo "All files processed successfully!"