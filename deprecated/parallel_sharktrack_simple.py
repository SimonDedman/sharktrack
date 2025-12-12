#!/usr/bin/env python3
"""
Simplified Parallel SharkTrack Analysis (Working Version)
"""

import os
import sys
import argparse
import multiprocessing
import concurrent.futures
import subprocess
import time
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime, timedelta

def analyze_single_video(video_file: Path, output_dir: Path, worker_id: int, position: int, total: int, config: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze a single video using subprocess"""
    try:
        print(f"[Worker {worker_id:2d}] {position:3d}/{total}: {video_file.name} - Starting analysis")

        start_time = time.time()

        # Create worker-specific output directory
        worker_output = output_dir / f"worker_{worker_id}" / video_file.stem
        worker_output.mkdir(parents=True, exist_ok=True)

        # Build command for SharkTrack analysis
        cmd = [
            "sharktrack-env/bin/python3", "app.py",
            "--input", str(video_file),
            "--output", str(worker_output),
            "--chapters"  # Explicitly provide flag to avoid prompt
        ]

        # Add other config parameters
        if config.get("peek", False):
            cmd.append("--peek")
        if config.get("conf"):
            cmd.extend(["--conf", str(config["conf"])])

        # Run SharkTrack analysis as subprocess
        env = os.environ.copy()
        env["PYTHONPATH"] = "."

        result = subprocess.run(
            cmd,
            cwd=os.getcwd(),
            env=env,
            capture_output=True,
            text=True,
            input="n\n",  # Provide "n" answer to chapters prompt
            timeout=600  # 10 minute timeout per video
        )

        processing_time = time.time() - start_time

        if result.returncode == 0:
            print(f"[Worker {worker_id:2d}] {position:3d}/{total}: {video_file.name} - ✅ Completed ({processing_time:.1f}s)")
            return {
                'success': True,
                'video_file': str(video_file),
                'processing_time': processing_time,
                'worker_id': worker_id,
                'output_dir': str(worker_output)
            }
        else:
            error_msg = result.stderr.strip() if result.stderr else f"Process failed with code {result.returncode}"
            print(f"[Worker {worker_id:2d}] {position:3d}/{total}: {video_file.name} - ❌ Failed: {error_msg[:80]}")
            return {
                'success': False,
                'video_file': str(video_file),
                'error': error_msg,
                'worker_id': worker_id
            }

    except Exception as e:
        print(f"[Worker {worker_id:2d}] {position:3d}/{total}: {video_file.name} - ❌ Exception: {e}")
        return {
            'success': False,
            'video_file': str(video_file),
            'error': str(e),
            'worker_id': worker_id
        }

def consolidate_results(output_dir: Path, worker_results: List[Dict[str, Any]]) -> None:
    """Consolidate results from all workers into unified output"""
    print(f"\n📁 Consolidating results from {len(set(r['worker_id'] for r in worker_results if r['success']))} workers...")

    consolidated_dir = output_dir / "consolidated"
    consolidated_dir.mkdir(exist_ok=True)

    successful_results = [r for r in worker_results if r['success']]

    if not successful_results:
        print("⚠️  No successful results to consolidate")
        return

    # Try to import pandas for proper consolidation
    try:
        import pandas as pd
        import shutil

        # Initialize combined data structures
        all_detections = []
        all_overviews = []
        processing_stats = []
        detection_images_dir = consolidated_dir / "detection_images"
        detection_images_dir.mkdir(exist_ok=True)

        print(f"🔄 Processing {len(successful_results)} successful video results...")

        # Process each worker's results
        for i, result in enumerate(successful_results):
            video_name = Path(result['video_file']).stem
            worker_output = Path(result['output_dir'])

            print(f"   📊 Processing {i+1}/{len(successful_results)}: {video_name}")

            # Collect processing statistics
            processing_stats.append({
                'video_name': video_name,
                'processing_time': result['processing_time'],
                'worker_id': result['worker_id']
            })

            # Look for internal_results directory
            internal_results = worker_output / "internal_results"

            if not internal_results.exists():
                print(f"   ⚠️  No internal_results found for {video_name}")
                continue

            # Consolidate detection data (output.csv)
            output_csv = internal_results / "output.csv"
            if output_csv.exists():
                try:
                    detections_df = pd.read_csv(output_csv)
                    if not detections_df.empty:
                        all_detections.append(detections_df)
                        print(f"      ✅ Found {len(detections_df)} detections")
                    else:
                        print(f"      📭 No detections in this video")
                except Exception as e:
                    print(f"      ❌ Error reading detections: {e}")

            # Consolidate overview data (overview.csv)
            overview_csv = internal_results / "overview.csv"
            if overview_csv.exists():
                try:
                    overview_df = pd.read_csv(overview_csv)
                    if not overview_df.empty:
                        all_overviews.append(overview_df)
                        tracks_in_video = overview_df.get('tracks_found', [0]).sum() if 'tracks_found' in overview_df.columns else 0
                        print(f"      🎯 Found {tracks_in_video} tracks")
                except Exception as e:
                    print(f"      ❌ Error reading overview: {e}")

            # Copy detection images
            videos_dir = internal_results / "videos" / video_name
            if videos_dir.exists():
                video_images_dir = detection_images_dir / video_name
                video_images_dir.mkdir(exist_ok=True)

                image_count = 0
                for image_file in videos_dir.glob("*.jpg"):
                    try:
                        shutil.copy2(image_file, video_images_dir / image_file.name)
                        image_count += 1
                    except Exception as e:
                        print(f"      ⚠️  Failed to copy {image_file.name}: {e}")

                if image_count > 0:
                    print(f"      🖼️  Copied {image_count} detection images")

        # Create consolidated files
        print(f"\n💾 Creating consolidated output files...")

        # Combined detections CSV
        if all_detections:
            combined_detections = pd.concat(all_detections, ignore_index=True)
            combined_detections.to_csv(consolidated_dir / "output.csv", index=False)
            print(f"   ✅ Combined detections: {len(combined_detections)} total detections across {len(all_detections)} videos")

        # Combined overview CSV
        if all_overviews:
            combined_overview = pd.concat(all_overviews, ignore_index=True)
            combined_overview.to_csv(consolidated_dir / "overview.csv", index=False)
            print(f"   ✅ Combined overview: {len(combined_overview)} videos processed")

        # Processing statistics
        if processing_stats:
            processing_df = pd.DataFrame(processing_stats)
            processing_df.to_csv(consolidated_dir / "processing_stats.csv", index=False)

            total_processing_time = sum(r['processing_time'] for r in processing_stats)
            avg_processing_time = total_processing_time / len(processing_stats)

            print(f"   ⏱️  Processing stats: {total_processing_time:.1f}s total, {avg_processing_time:.1f}s average per video")

        # Create summary report
        summary_report = consolidated_dir / "summary_report.txt"
        with open(summary_report, 'w') as f:
            f.write("# SharkTrack Analysis Summary Report\\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\\n\\n")
            f.write(f"Total videos processed: {len(successful_results)}\\n")
            f.write(f"Total detections: {len(combined_detections) if all_detections else 0}\\n")
            f.write(f"Total processing time: {total_processing_time:.1f} seconds\\n")

        print(f"\\n✅ Consolidation complete!")
        print(f"   📊 Results: {consolidated_dir}")

    except ImportError:
        print("❌ pandas not available - creating basic consolidation")
        summary_file = consolidated_dir / "basic_summary.txt"
        with open(summary_file, 'w') as f:
            f.write("# Basic SharkTrack Results Summary\\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\\n\\n")
            f.write(f"Total videos processed: {len(successful_results)}\\n\\n")
            for result in successful_results:
                video_name = Path(result['video_file']).stem
                f.write(f"- {video_name}: {result['processing_time']:.1f}s (worker {result['worker_id']})\\n")
        print(f"✅ Basic consolidation complete: {summary_file}")

def parallel_sharktrack_analysis(input_dir: str, output_dir: str, workers: int = 0, peek_mode: bool = False) -> bool:
    """Run SharkTrack analysis in parallel across multiple workers"""

    # Auto-detect optimal workers if not specified
    if workers == 0:
        try:
            import psutil
            cpu_cores = multiprocessing.cpu_count()
            memory_gb = psutil.virtual_memory().total / (1024**3)
            auto_workers = min(cpu_cores, int(memory_gb // 4), 8)  # 4GB per worker for ML
            auto_workers = max(1, auto_workers)
            print(f"🧠 Auto-detected {auto_workers} optimal workers (CPU: {cpu_cores}, RAM: {memory_gb:.1f}GB)")
            workers = auto_workers
        except ImportError:
            workers = 4
            print(f"⚠️  Using fallback: {workers} workers")

    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Find video files
    video_files = []
    for ext in ['.MP4', '.mp4', '.MOV', '.mov']:
        video_files.extend(list(input_path.rglob(f'*{ext}')))

    if not video_files:
        print("❌ No video files found!")
        return False

    print(f"📹 Found {len(video_files)} video files for analysis")
    print(f"🔧 Using {workers} parallel workers")
    print(f"🧠 Mode: {'Peek (keyframe detection)' if peek_mode else 'Full tracking (MaxN computation)'}")

    # SharkTrack model configuration
    model_config = {
        "limit": len(video_files),
        "stereo_prefix": None,
        "chapters": False,
        "species_classifier": None,
        "conf": 0.25,
        "imgsz": 640,
        "peek": peek_mode
    }

    # Estimate processing time
    estimated_time_per_video = 60 if not peek_mode else 30  # seconds
    total_estimated_minutes = (len(video_files) * estimated_time_per_video) / (workers * 60)
    hours = int(total_estimated_minutes // 60)
    minutes = int(total_estimated_minutes % 60)

    completion_time = datetime.now() + timedelta(hours=hours, minutes=minutes)

    print(f"⏱️  Estimated duration: {hours:02d}:{minutes:02d} ({workers}x parallel)")
    print(f"🎯 Estimated completion: {completion_time.strftime('%H:%M:%S')}")

    # Create task list with worker IDs
    video_tasks = [(video_file, i+1, (i % workers) + 1) for i, video_file in enumerate(video_files)]

    start_time = time.time()
    results = []

    print(f"\\n🚀 Starting parallel analysis with {workers} workers...")

    # Simple parallel processing
    def worker_wrapper(args):
        video_file, position, worker_id = args
        return analyze_single_video(video_file, output_path, worker_id, position, len(video_files), model_config)

    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
        futures = [executor.submit(worker_wrapper, task) for task in video_tasks]

        for future in concurrent.futures.as_completed(futures):
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                print(f"❌ Task failed: {e}")
                results.append({'success': False, 'error': str(e)})

    # Calculate final statistics
    total_time = time.time() - start_time
    successful = sum(1 for r in results if r.get('success', False))

    total_minutes = total_time / 60
    hours = int(total_minutes // 60)
    minutes = int(total_minutes % 60)

    throughput_per_minute = successful / total_minutes if total_minutes > 0 else 0

    print(f"\\n✅ Parallel SharkTrack analysis completed!")
    print(f"   • Total time: {hours:02d}:{minutes:02d}")
    print(f"   • Successful: {successful}/{len(video_files)}")
    print(f"   • Throughput: {throughput_per_minute:.2f} videos/minute")
    print(f"   • Speedup: ~{workers:.1f}x vs sequential processing")

    # Consolidate results
    if successful > 0:
        consolidate_results(output_path, results)

    return successful > 0

def main():
    parser = argparse.ArgumentParser(description='Simplified Parallel SharkTrack Analysis')

    parser.add_argument('input_dir', help='Directory containing converted video files')
    parser.add_argument('output_dir', help='Output directory for analysis results')
    parser.add_argument('--workers', '-w', type=int, default=0,
                       help='Number of parallel workers (0 = auto-detect)')
    parser.add_argument('--peek', action='store_true',
                       help='Use peek mode for faster keyframe detection')

    args = parser.parse_args()

    # Validate paths
    if not Path(args.input_dir).exists():
        print(f"❌ Input directory does not exist: {args.input_dir}")
        return 1

    print(f"🎯 Simplified Parallel SharkTrack Analysis")
    print(f"   • Input: {args.input_dir}")
    print(f"   • Output: {args.output_dir}")
    print(f"   • Workers: {args.workers or 'auto-detect'}")
    print(f"   • Mode: {'Peek' if args.peek else 'Full tracking'}")

    success = parallel_sharktrack_analysis(
        args.input_dir,
        args.output_dir,
        workers=args.workers,
        peek_mode=args.peek
    )

    if success:
        print(f"\\n🎉 Analysis complete! Results saved to: {args.output_dir}")
        return 0
    else:
        print(f"\\n❌ Analysis failed!")
        return 1

if __name__ == "__main__":
    exit(main())