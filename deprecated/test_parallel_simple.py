#!/usr/bin/env python3
"""
Simple test of parallel SharkTrack analysis
"""

import concurrent.futures
import subprocess
import time
from pathlib import Path

def analyze_video(video_file):
    """Simple video analysis function"""
    print(f"Starting: {video_file.name}")

    result = subprocess.run([
        'sharktrack-env/bin/python3', 'app.py',
        '--input', str(video_file),
        '--output', f'./test_output/{video_file.stem}',
        '--chapters'
    ], capture_output=True, text=True, input='n\n', timeout=300)

    if result.returncode == 0:
        print(f"✅ Completed: {video_file.name}")
        return {'success': True, 'video': str(video_file)}
    else:
        print(f"❌ Failed: {video_file.name} - {result.stderr[:100]}")
        return {'success': False, 'video': str(video_file), 'error': result.stderr}

def main():
    # Test with just 3 videos and 2 workers
    video_dir = Path("/media/simon/SSK SSD1/converted_output_final/converted")
    video_files = list(video_dir.glob("*.MP4"))[:3]  # Just first 3 videos

    print(f"Testing parallel analysis with {len(video_files)} videos:")
    for vf in video_files:
        print(f"  - {vf.name}")

    # Create output directory
    Path('./test_output').mkdir(exist_ok=True)

    # Run parallel
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(analyze_video, vf) for vf in video_files]

        results = []
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            results.append(result)

    # Summary
    successful = sum(1 for r in results if r['success'])
    print(f"\nResults: {successful}/{len(results)} successful")

if __name__ == "__main__":
    main()