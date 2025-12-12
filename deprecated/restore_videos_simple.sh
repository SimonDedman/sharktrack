#!/bin/bash

# Function to find original location of a video
find_original() {
    local video_name="$1"
    find "/media/simon/SSK SSD1/BRUV_"* -name "$video_name" -type f 2>/dev/null | head -1
}

converted_dir="/media/simon/SSK SSD1/converted_output_final/converted"
moved_count=0
failed_count=0
backed_up_count=0

echo "🔄 Starting video restoration..."

for converted_video in "$converted_dir"/*.MP4; do
    [ ! -f "$converted_video" ] && continue
    
    video_name=$(basename "$converted_video")
    echo -n "Processing $video_name... "
    
    # Find original location
    original_path=$(find_original "$video_name")
    
    if [ -z "$original_path" ]; then
        echo "❌ Original not found"
        ((failed_count++))
        continue
    fi
    
    # Create backup if original exists
    if [ -f "$original_path" ]; then
        backup_path="${original_path}.original"
        if [ ! -f "$backup_path" ]; then
            cp "$original_path" "$backup_path"
            ((backed_up_count++))
        fi
    fi
    
    # Replace with converted version
    cp "$converted_video" "$original_path"
    echo "✅ Restored to $(dirname "$original_path" | sed 's|.*/||')"
    ((moved_count++))
done

echo ""
echo "✅ Video restoration complete!"
echo "   • Successfully restored: $moved_count videos"
echo "   • Failed restorations: $failed_count"
echo "   • Original files backed up: $backed_up_count"
