#!/usr/bin/env python3
"""
Reorganize analysis results from worker-based structure to proper BRUV directory structure
"""

import os
import shutil
from pathlib import Path

def find_original_video_directory(video_name: str, search_root: str = "/media/simon/SSK SSD1/") -> Path:
    """Find the original BRUV directory for a given video file"""
    try:
        # Search for the original video file in BRUV directories
        search_path = Path(search_root)
        for bruv_dir in search_path.glob("BRUV_*"):
            for video_path in bruv_dir.rglob(video_name):
                if video_path.is_file():
                    return video_path.parent  # Return the directory containing the video

        # Fallback: if not found, return a default location
        print(f"⚠️  Could not find original directory for {video_name}")
        return Path(search_root) / "orphaned_analysis_results"
    except Exception as e:
        print(f"❌ Error searching for {video_name}: {e}")
        return Path(search_root) / "orphaned_analysis_results"

def reorganize_analysis_results():
    """Move analysis results from worker folders to proper BRUV directories"""

    analysis_root = Path("/media/simon/SSK SSD1/analysis_results")

    # Find all worker directories
    worker_dirs = list(analysis_root.glob("worker_*"))

    print(f"🔄 Found {len(worker_dirs)} worker directories to reorganize")

    moved_count = 0
    failed_count = 0

    for worker_dir in worker_dirs:
        print(f"\n📂 Processing {worker_dir.name}...")

        # Find all video result directories in this worker folder
        video_dirs = [d for d in worker_dir.iterdir() if d.is_dir()]

        for video_dir in video_dirs:
            video_name = video_dir.name
            video_file = f"{video_name}.MP4"

            try:
                # Find the original BRUV directory for this video
                original_bruv_dir = find_original_video_directory(video_file)

                # Create analysis_results directory in the original location
                target_analysis_dir = original_bruv_dir / "analysis_results"
                target_analysis_dir.mkdir(parents=True, exist_ok=True)

                # Target path for this video's results
                target_video_dir = target_analysis_dir / video_name

                # Move the entire video results directory
                if target_video_dir.exists():
                    print(f"   ⚠️  Target exists, removing old: {target_video_dir}")
                    shutil.rmtree(target_video_dir)

                shutil.move(str(video_dir), str(target_video_dir))
                print(f"   ✅ Moved {video_name} to {target_video_dir}")
                moved_count += 1

            except Exception as e:
                print(f"   ❌ Failed to move {video_name}: {e}")
                failed_count += 1

        # Remove empty worker directory if all videos were moved successfully
        try:
            if not any(worker_dir.iterdir()):
                worker_dir.rmdir()
                print(f"   🗑️  Removed empty worker directory: {worker_dir.name}")
            else:
                print(f"   📁 Worker directory not empty, keeping: {worker_dir.name}")
        except Exception as e:
            print(f"   ⚠️  Could not remove worker directory: {e}")

    print(f"\n✅ Reorganization complete!")
    print(f"   • Successfully moved: {moved_count} video results")
    print(f"   • Failed moves: {failed_count}")

    # Show sample of new structure
    print(f"\n📋 Sample of new structure:")
    bruv_dirs = list(Path("/media/simon/SSK SSD1/").glob("BRUV_*"))
    for bruv_dir in bruv_dirs[:2]:  # Show first 2 BRUV directories
        analysis_dir = bruv_dir / "analysis_results"
        if analysis_dir.exists():
            video_results = list(analysis_dir.iterdir())[:3]  # Show first 3 videos
            print(f"   {bruv_dir.name}/analysis_results/")
            for video_result in video_results:
                if video_result.is_dir():
                    print(f"   ├── {video_result.name}/")

if __name__ == "__main__":
    reorganize_analysis_results()