#!/usr/bin/env python3
"""
Move converted videos back to their original BRUV directories, replacing the originals
This simulates what would have happened with --convert-replace
"""

import os
import shutil
from pathlib import Path

def find_original_video_location(video_name: str, search_root: str = "/media/simon/SSK SSD1/") -> Path:
    """Find the original location of a video file in BRUV directories"""
    try:
        search_path = Path(search_root)

        # First try accessible collections without I/O errors
        accessible_collections = [
            "BRUV_Summer_2022_1_45",
            "BRUV_Winter_2021_103_105"
        ]

        for collection in accessible_collections:
            collection_path = search_path / collection
            if collection_path.exists():
                try:
                    for video_path in collection_path.rglob(video_name):
                        if video_path.is_file():
                            return video_path
                except Exception:
                    continue

        # Try BRUV_Summer_2022_46_62 with known accessible BRUV directories
        problematic_collection = search_path / "BRUV_Summer_2022_46_62"
        if problematic_collection.exists():
            # Known accessible BRUV directories from scan
            accessible_bruv_dirs = [46, 47, 48, 49, 50, 51, 52, 54, 55, 56, 57, 58, 59, 60, 61, 62]

            for bruv_num in accessible_bruv_dirs:
                try:
                    bruv_dir = problematic_collection / f"BRUV {bruv_num}"
                    video_path = bruv_dir / video_name
                    if video_path.exists():
                        return video_path
                except Exception:
                    continue

        print(f"⚠️  Could not find original location for {video_name}")
        return None
    except Exception as e:
        print(f"❌ Error searching for {video_name}: {e}")
        return None

def check_filesystem_writable():
    """Check if the SSD filesystem is writable"""
    try:
        test_file = Path("/media/simon/SSK SSD1/.write_test")
        test_file.touch()
        test_file.unlink()
        return True
    except (PermissionError, OSError):
        return False

def restore_converted_videos():
    """Move converted videos back to their original BRUV directories"""

    # Check if filesystem is writable
    dry_run = not check_filesystem_writable()
    if dry_run:
        print("⚠️  SSD filesystem is read-only due to I/O errors")
        print("   Running in DRY-RUN mode - showing what would be restored")
        print("   To fix: sudo umount '/media/simon/SSK SSD1' && sudo mount -o rw /dev/sda2 '/media/simon/SSK SSD1'")
        print("   Or reconnect the SSD to trigger filesystem check\n")

    converted_dir = Path("/media/simon/SSK SSD1/converted_output_final/converted")

    if not converted_dir.exists():
        print(f"❌ Converted directory not found: {converted_dir}")
        return

    # Find all converted videos
    converted_videos = list(converted_dir.glob("*.MP4")) + list(converted_dir.glob("*.mp4"))

    print(f"🔄 Found {len(converted_videos)} converted videos to restore")

    moved_count = 0
    failed_count = 0
    backed_up_count = 0

    for converted_video in converted_videos:
        video_name = converted_video.name

        try:
            # Find the original location
            original_location = find_original_video_location(video_name)

            if original_location is None:
                print(f"   ❌ Skipping {video_name} - original location not found")
                failed_count += 1
                continue

            if dry_run:
                # Dry run mode - just show what would happen
                if original_location.exists():
                    print(f"   📋 Would backup original: {video_name}.original")
                    backed_up_count += 1
                print(f"   📋 Would restore {video_name} to {original_location.parent.name}")
                moved_count += 1
            else:
                # Create backup of original if it still exists
                if original_location.exists():
                    backup_path = original_location.with_suffix(original_location.suffix + ".original")
                    if not backup_path.exists():  # Don't overwrite existing backups
                        shutil.copy2(original_location, backup_path)
                        print(f"   💾 Backed up original: {video_name}.original")
                        backed_up_count += 1

                # Replace the original with the converted version
                shutil.copy2(converted_video, original_location)
                print(f"   ✅ Restored {video_name} to {original_location.parent.name}")
                moved_count += 1

        except Exception as e:
            print(f"   ❌ Failed to restore {video_name}: {e}")
            failed_count += 1

    if dry_run:
        print(f"\n📋 Dry-run analysis complete!")
        print(f"   • Videos that can be restored: {moved_count}")
        print(f"   • Videos not found: {failed_count}")
        print(f"   • Originals that would be backed up: {backed_up_count}")
    else:
        print(f"\n✅ Video restoration complete!")
        print(f"   • Successfully restored: {moved_count} videos")
        print(f"   • Failed restorations: {failed_count}")
        print(f"   • Original files backed up: {backed_up_count}")

    # Check if we should remove the converted directory
    if moved_count > 0 and failed_count == 0:
        try:
            print(f"\n🗑️  All videos successfully restored. You can now remove:")
            print(f"     {converted_dir}")
            print(f"     rm -rf '{converted_dir}'")
        except Exception as e:
            print(f"   ⚠️  Note: {converted_dir} can be manually removed")

    # Show sample of new structure
    print(f"\n📋 Sample of restored structure:")
    bruv_dirs = list(Path("/media/simon/SSK SSD1/").glob("BRUV_*"))
    for bruv_dir in bruv_dirs[:2]:  # Show first 2 BRUV directories
        video_files = list(bruv_dir.rglob("*.MP4"))[:3]  # Show first 3 videos
        if video_files:
            print(f"   {bruv_dir.name}/")
            for bruv_subdir in bruv_dir.iterdir():
                if bruv_subdir.is_dir() and bruv_subdir.name.startswith("BRUV"):
                    videos_in_subdir = list(bruv_subdir.glob("*.MP4"))[:2]
                    if videos_in_subdir:
                        print(f"   ├── {bruv_subdir.name}/")
                        for video in videos_in_subdir:
                            print(f"   │   ├── {video.name}")
                        # Check for analysis results
                        analysis_dir = bruv_subdir / "analysis_results"
                        if analysis_dir.exists():
                            print(f"   │   └── analysis_results/")

if __name__ == "__main__":
    restore_converted_videos()