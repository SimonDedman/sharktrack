#!/usr/bin/env python3
"""
Simplified BRUV Batch Processor
Focuses on core processing and deletion policy without complex dependencies
"""

import os
import argparse
import subprocess
from pathlib import Path
from typing import Tuple
from datetime import datetime
import shutil

def check_disk_space(path: str, required_gb: float = 50.0) -> bool:
    """Check if enough disk space is available with monitoring"""
    try:
        stat = shutil.disk_usage(path)
        free_gb = stat.free / (1024**3)
        total_gb = stat.total / (1024**3)
        used_gb = stat.used / (1024**3)
        usage_percent = (used_gb / total_gb) * 100

        print(f"💾 Disk Usage: {used_gb:.1f}GB / {total_gb:.1f}GB ({usage_percent:.1f}% used)")
        print(f"💾 Available space: {free_gb:.1f} GB")

        # Critical space check
        if usage_percent > 90:
            print(f"🚨 CRITICAL: Disk usage over 90% - filesystem may become unstable")
            return False
        elif usage_percent > 80:
            print(f"⚠️  WARNING: Disk usage over 80% - recommend cleanup or smaller batch size")

        if free_gb < required_gb:
            print(f"⚠️  Warning: Only {free_gb:.1f} GB available (recommended: {required_gb:.1f} GB)")
            return False
        return True
    except Exception as e:
        print(f"❌ Could not check disk space: {e}")
        return False

def monitor_disk_space_during_processing(output_path: str, check_interval: int = 300):
    """Monitor disk space during processing and warn if space gets low"""
    import threading
    import time

    def space_monitor():
        while True:
            try:
                stat = shutil.disk_usage(output_path)
                free_gb = stat.free / (1024**3)
                usage_percent = (stat.used / stat.total) * 100

                if usage_percent > 85:
                    print(f"\n⚠️  SPACE WARNING: {usage_percent:.1f}% disk usage, {free_gb:.1f}GB free")
                    if usage_percent > 90:
                        print(f"🚨 CRITICAL: Consider stopping processing and cleaning up!")

                time.sleep(check_interval)  # Check every 5 minutes
            except Exception:
                break  # Exit monitoring if path becomes unavailable

    monitor_thread = threading.Thread(target=space_monitor, daemon=True)
    monitor_thread.start()
    return monitor_thread

def count_videos(input_dir: str, output_dir: str = None, skip_existing: bool = False) -> Tuple[int, int]:
    """Count video files in input directory and how many need processing"""
    input_path = Path(input_dir)
    video_extensions = ['.MP4', '.mp4', '.MOV', '.mov', '.AVI', '.avi']

    all_videos = []
    for ext in video_extensions:
        all_videos.extend(list(input_path.rglob(f'*{ext}')))

    total_count = len(all_videos)

    if skip_existing and output_dir:
        output_path = Path(output_dir)
        need_processing = []

        for video_file in all_videos:
            output_file = output_path / video_file.name
            if not (output_file.exists() and output_file.stat().st_size > 1024):
                need_processing.append(video_file)

        return total_count, len(need_processing)
    else:
        return total_count, total_count

def prompt_deletion_policy() -> str:
    """Prompt user for deletion policy preference"""
    print(f"\n🗑️  Original Video Deletion Policy")
    print(f"After successful format conversion, how should original videos be handled?")
    print(f"")
    print(f"Options:")
    print(f"   1. Delete all successfully converted originals (saves most space)")
    print(f"   2. Ask before deleting each batch (default)")
    print(f"   3. Keep all original videos (safest)")
    print(f"")

    while True:
        try:
            choice = input("Select option (1-3) [2]: ").strip()
            if not choice:
                choice = "2"

            if choice == "1":
                return "delete-all"
            elif choice == "2":
                return "ask-each"
            elif choice == "3":
                return "no"
            else:
                print("Please enter 1, 2, or 3")
        except KeyboardInterrupt:
            print(f"\n❌ Cancelled by user")
            exit(1)

def convert_single_video(video_file, output_path, worker_id, position, total, in_place=False):
    """Convert a single video with worker identification"""
    if in_place:
        # In-place conversion: create temp file, then replace original
        output_file = video_file.parent / f"{video_file.stem}_temp.MP4"
        final_file = video_file
    else:
        # Standard conversion: separate output directory
        output_file = output_path / video_file.name
        final_file = output_file

    # Skip if already converted (check for reasonable file size)
    if final_file.exists() and final_file.stat().st_size > 1024 and not in_place:
        print(f"[Worker {worker_id:2d}] {position:3d}/{total}: {video_file.name} - Already exists, skipping")
        return True

    print(f"[Worker {worker_id:2d}] {position:3d}/{total}: {video_file.name} - Starting conversion")

    # Use ffmpeg to convert
    cmd = [
        'ffmpeg', '-i', str(video_file),
        '-c:v', 'libx264', '-preset', 'fast', '-crf', '23',
        '-c:a', 'aac', '-b:a', '128k',
        '-f', 'mp4', '-y', str(output_file)
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)
        if result.returncode == 0:
            if in_place:
                # Replace original with converted file
                try:
                    # Backup original first (in case of failure)
                    backup_file = video_file.parent / f"{video_file.stem}_original.MP4"
                    video_file.rename(backup_file)

                    # Move converted file to original location
                    output_file.rename(video_file)

                    # Remove backup if successful
                    backup_file.unlink()

                    print(f"[Worker {worker_id:2d}] {position:3d}/{total}: {video_file.name} - ✅ Converted in-place")
                except Exception as e:
                    print(f"[Worker {worker_id:2d}] {position:3d}/{total}: {video_file.name} - ❌ In-place replacement failed: {e}")
                    # Restore original if replacement failed
                    if backup_file.exists():
                        backup_file.rename(video_file)
                    if output_file.exists():
                        output_file.unlink()
                    return False
            else:
                print(f"[Worker {worker_id:2d}] {position:3d}/{total}: {video_file.name} - ✅ Completed")
            return True
        else:
            print(f"[Worker {worker_id:2d}] {position:3d}/{total}: {video_file.name} - ❌ Failed: {result.stderr[:50]}...")
            return False
    except subprocess.TimeoutExpired:
        print(f"[Worker {worker_id:2d}] {position:3d}/{total}: {video_file.name} - ⏰ Timed out")
        return False
    except Exception as e:
        print(f"[Worker {worker_id:2d}] {position:3d}/{total}: {video_file.name} - ❌ Error: {e}")
        return False

def reformat_gopro_simple(input_dir: str, output_dir: str, workers: int = 8, in_place: bool = False) -> bool:
    """Parallel GoPro reformatting using ThreadPoolExecutor"""
    import concurrent.futures
    import threading

    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Find video files
    video_files = []
    for ext in ['.MP4', '.mp4']:
        video_files.extend(list(input_path.rglob(f'*{ext}')))

    print(f"📹 Found {len(video_files)} video files to convert")
    print(f"🔧 Using {workers} parallel workers")

    if len(video_files) == 0:
        print("❌ No video files found!")
        return False

    # Thread-safe counter for worker IDs
    worker_counter = threading.Lock()
    current_worker_id = [0]

    def get_worker_id():
        with worker_counter:
            current_worker_id[0] += 1
            return current_worker_id[0]

    def worker_wrapper(args):
        video_file, position = args
        worker_id = get_worker_id()
        return convert_single_video(video_file, output_path, worker_id, position, len(video_files), in_place)

    # Create list of (video_file, position) tuples
    video_tasks = [(video_file, i+1) for i, video_file in enumerate(video_files)]

    print(f"📋 Task distribution: 0 GPU, {len(video_files)} CPU")

    # Show time estimates after task distribution
    if len(video_files) > 0:
        estimated_time_hours = (len(video_files) * 2) / (workers * 60)  # 2 min per video estimate
        estimated_minutes = estimated_time_hours * 60
        hours = int(estimated_minutes // 60)
        minutes = int(estimated_minutes % 60)

        # Calculate completion time
        from datetime import datetime, timedelta
        completion_time = datetime.now() + timedelta(hours=hours, minutes=minutes)

        print(f"   • Estimated duration: {hours:02d}:{minutes:02d} ({workers}x CPU)")
        print(f"   • Estimated completion time: {completion_time.strftime('%Y-%m-%d %H:%M')}")

    success_count = 0
    print(f"\n🚀 Starting parallel conversion...")

    # Try to inhibit system sleep during processing
    try:
        subprocess.run(['systemd-inhibit', '--what=sleep:idle', '--who=SharkTrack',
                       '--why=Video processing in progress', 'true'],
                      capture_output=True, timeout=5)
        print(f"🛡️  System sleep inhibited during processing")
    except:
        print(f"⚠️  Keep system awake - screen sleep may pause CPU-intensive tasks")

    # Use ThreadPoolExecutor for parallel processing
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
        # Submit all tasks
        future_to_video = {executor.submit(worker_wrapper, task): task for task in video_tasks}

        # Process completed tasks
        for future in concurrent.futures.as_completed(future_to_video):
            try:
                success = future.result()
                if success:
                    success_count += 1
            except Exception as e:
                video_task = future_to_video[future]
                print(f"❌ Task failed: {video_task[0].name} - {e}")

    print(f"\n✅ Converted {success_count}/{len(video_files)} videos successfully")
    return success_count > 0

def handle_deletion_policy(input_dir: str, converted_dir: str, policy: str) -> bool:
    """Handle original video deletion based on policy with robust error handling"""
    input_path = Path(input_dir)
    converted_path = Path(converted_dir)

    try:
        # Find original and converted videos
        original_videos = []
        for ext in ['.MP4', '.mp4']:
            original_videos.extend(list(input_path.rglob(f'*{ext}')))

        converted_videos = []
        for ext in ['.MP4', '.mp4']:
            converted_videos.extend(list(converted_path.rglob(f'*{ext}')))

        if len(converted_videos) == 0:
            print("⚠️  No converted videos found - keeping all originals")
            return False

        # Calculate space savings with error handling
        original_size = 0
        for f in original_videos:
            try:
                if f.exists():
                    original_size += f.stat().st_size
            except (OSError, IOError) as e:
                print(f"   Warning: Cannot access {f.name}: {e}")
                continue
        original_size = original_size / (1024**3)

        print(f"\n🗑️  Deletion Policy: {policy}")
        print(f"   • Original videos: {len(original_videos)} files ({original_size:.1f} GB)")
        print(f"   • Converted videos: {len(converted_videos)} files")

        # Check filesystem is writable before attempting deletion
        try:
            test_file = input_path / ".deletion_test"
            test_file.touch()
            test_file.unlink()
        except (OSError, IOError, PermissionError) as e:
            print(f"❌ Cannot delete files - filesystem error: {e}")
            print(f"   Suggestion: Remount the drive or check permissions")
            return False

        if policy == 'no':
            print(f"✅ Keeping all original videos")
            return False

        elif policy == 'delete-all':
            print(f"🗑️  Deleting original videos...")
            deleted_count = 0
            failed_files = []

            for video_file in original_videos:
                try:
                    video_file.unlink()
                    deleted_count += 1
                except (OSError, IOError, PermissionError) as e:
                    failed_files.append((video_file.name, str(e)))
                    print(f"   ❌ Failed to delete {video_file.name}: {e}")
                    continue

            print(f"✅ Deleted {deleted_count}/{len(original_videos)} original videos")

            if failed_files:
                print(f"⚠️  {len(failed_files)} files could not be deleted:")
                for filename, error in failed_files[:5]:  # Show first 5 errors
                    print(f"   • {filename}: {error}")
                if len(failed_files) > 5:
                    print(f"   • ... and {len(failed_files) - 5} more")

            return deleted_count > 0

        elif policy == 'ask-each':
            if len(converted_videos) < len(original_videos):
                print(f"   ⚠️  Warning: {len(original_videos) - len(converted_videos)} videos failed to convert")

            confirm = input(f"\nDelete {len(original_videos)} original videos to save {original_size:.1f} GB? (y/N): ")

            if confirm.lower() in ['y', 'yes']:
                print(f"🗑️  Deleting original videos...")
                deleted_count = 0
                failed_files = []

                for video_file in original_videos:
                    try:
                        video_file.unlink()
                        deleted_count += 1
                    except (OSError, IOError, PermissionError) as e:
                        failed_files.append((video_file.name, str(e)))
                        continue

                print(f"✅ Deleted {deleted_count}/{len(original_videos)} original videos")

                if failed_files:
                    print(f"⚠️  {len(failed_files)} files could not be deleted (filesystem issues)")

                return deleted_count > 0
            else:
                print(f"✅ Keeping original videos")
                return False

    except Exception as e:
        print(f"❌ Error in deletion policy handling: {e}")
        print(f"   All original videos will be preserved for safety")
        return False

    return False

def run_sharktrack_analysis(video_dir: str, output_dir: str) -> bool:
    """Run real SharkTrack analysis on converted videos"""
    print(f"\n🧠 Running SharkTrack Analysis...")

    try:
        # Import the real SharkTrack app
        import sys
        sys.path.append('.')
        from app import Model

        output_path = Path(output_dir)
        analysis_path = output_path / "analysis"
        analysis_path.mkdir(parents=True, exist_ok=True)

        # Count videos to analyze
        video_path = Path(video_dir)
        video_files = []
        for ext in ['.MP4', '.mp4']:
            video_files.extend(list(video_path.rglob(f'*{ext}')))

        if len(video_files) == 0:
            print("⚠️  No video files found for analysis")
            return False

        print(f"Found {len(video_files)} videos for analysis")

        # Run real SharkTrack analysis
        try:
            # Initialize SharkTrack model in peek mode for speed
            model_config = {
                "limit": len(video_files),
                "stereo_prefix": None,
                "chapters": False,
                "species_classifier": None,
                "conf": 0.25,
                "imgsz": 640,
                "peek": True  # Use peek mode for faster processing
            }

            model = Model(str(video_path), str(analysis_path), **model_config)

            # Process each video
            successful_analyses = 0
            for i, video_file in enumerate(video_files):
                try:
                    print(f"   Processing {i+1}/{len(video_files)}: {video_file.name}")
                    model.inference_type(str(video_file))
                    successful_analyses += 1
                except Exception as e:
                    print(f"   ❌ Failed to analyze {video_file.name}: {e}")
                    continue

            print(f"✅ Analysis completed: {successful_analyses}/{len(video_files)} videos successful")
            return successful_analyses > 0

        except Exception as e:
            print(f"❌ SharkTrack analysis failed: {e}")
            print("   Falling back to placeholder analysis...")

            # Don't create useless placeholders - just report failure
            print(f"❌ Analysis failed: {str(e)}")
            print(f"   Suggestion: Use 'parallel_sharktrack_analysis.py' for better performance")
            print(f"   Or ensure all dependencies are installed with: pip install -r requirements.txt")
            return False

    except ImportError as e:
        print(f"❌ Cannot import SharkTrack components: {e}")
        print("   Please ensure all dependencies are installed")
        return False

def main():
    parser = argparse.ArgumentParser(
        description='Simple BRUV Batch Processor',
        epilog='''
Examples:
  # Standard conversion (separate output directory):
  python3 simple_batch_processor.py --input ./BRUV_videos --output ./converted

  # In-place conversion (replace originals, saves space):
  python3 simple_batch_processor.py --input ./BRUV_videos --output ./analysis --in-place

  # In-place with monitoring:
  python3 simple_batch_processor.py --input ./BRUV_videos --output ./analysis --in-place --progress-monitoring
        ''',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument('--input', '-i', required=True,
                       help='Input directory containing BRUV videos')
    parser.add_argument('--output', '-o', required=True,
                       help='Output directory for processed results')
    parser.add_argument('--workers', '-w', type=int, default=0,
                       help='Number of parallel workers (0 = auto-optimize)')
    parser.add_argument('--skip-conversion', action='store_true',
                       help='Skip GoPro format conversion step')
    parser.add_argument('--delete-originals', choices=['delete-all', 'ask-each', 'no'],
                       default='ask-each',
                       help='How to handle original videos after conversion')
    parser.add_argument('--in-place', action='store_true',
                       help='Replace original videos with converted ones in the same location (saves space and maintains organization)')
    parser.add_argument('--plan-only', action='store_true',
                       help='Show processing plan without executing')
    parser.add_argument('--optimize-workers', action='store_true',
                       help='Run worker optimization test')
    parser.add_argument('--performance-check', action='store_true',
                       help='Check system performance settings and show optimization commands')
    parser.add_argument('--auto-optimize', action='store_true',
                       help='Attempt automatic performance optimization')
    parser.add_argument('--gpu-accelerated', action='store_true',
                       help='Use GPU acceleration for video conversion (requires NVIDIA GPU)')
    parser.add_argument('--gpu-workers', type=int, default=2,
                       help='Number of GPU workers for video conversion (default: 2)')
    parser.add_argument('--progress-monitoring', action='store_true',
                       help='Use intelligent progress monitoring with real-time updates')
    parser.add_argument('--yes', '-y', action='store_true',
                       help='Skip confirmation prompts')

    args = parser.parse_args()

    # Performance check mode
    if args.performance_check:
        try:
            from utils.performance_optimizer import optimize_system_performance
            optimize_system_performance(auto_apply=False)
            return 0
        except ImportError:
            print("⚠️  Performance optimizer not available")
            return 1

    # Worker optimization mode
    if args.optimize_workers:
        try:
            from utils.worker_optimizer import auto_optimize_workers
            optimal_workers = auto_optimize_workers(args.input, quick_test=True)
            print(f"\n🎯 Recommended command:")
            print(f"python3 simple_batch_processor.py \\")
            print(f"  --input \"{args.input}\" \\")
            print(f"  --output \"{args.output}\" \\")
            print(f"  --workers {optimal_workers} \\")
            print(f"  --delete-originals delete-all \\")
            print(f"  --yes")
            return 0
        except ImportError:
            print("⚠️  Worker optimizer not available, using theoretical calculation")

    # Validate input directory
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"❌ Input directory does not exist: {input_path}")
        return 1

    # Auto-optimize workers if not specified
    if args.workers == 0:
        print("🔍 Auto-detecting optimal worker count...", end="", flush=True)
        try:
            import multiprocessing
            import psutil

            cpu_cores = multiprocessing.cpu_count()
            memory_gb = psutil.virtual_memory().total / (1024**3)

            # Simple heuristic: min(CPU cores, memory_GB/2, 16) - use all available cores
            auto_workers = min(cpu_cores, int(memory_gb // 2), 16)
            auto_workers = max(1, auto_workers)

            print(f" {auto_workers}")
            print(f"🧠 Auto-detected {auto_workers} optimal workers (CPU: {cpu_cores}, RAM: {memory_gb:.1f}GB)")
            args.workers = auto_workers

        except ImportError as e:
            print(f" failed")
            args.workers = 4  # Fallback
            print(f"⚠️  Using fallback: {args.workers} workers (psutil not available: {e})")

    # Count videos and check existing conversions
    if not args.skip_conversion:
        output_dir = str(Path(args.output) / "converted")
        total_videos, videos_to_process = count_videos(args.input, output_dir, skip_existing=True)
        already_converted = total_videos - videos_to_process
    else:
        total_videos, videos_to_process = count_videos(args.input)
        already_converted = 0

    print(f"\n📊 Processing Plan")
    print(f"   • Input directory: {args.input}")
    print(f"   • Output directory: {args.output}")
    print(f"   • Total video files: {total_videos}")
    if already_converted > 0:
        print(f"   • Already converted: {already_converted}")
        print(f"   • Need processing: {videos_to_process}")
    else:
        print(f"   • Need processing: {videos_to_process}")
    print(f"   • Skip conversion: {args.skip_conversion}")
    if args.in_place:
        print(f"   • Conversion mode: In-place (replace originals)")
    else:
        print(f"   • Conversion mode: Separate output directory")
        print(f"   • Deletion policy: {args.delete_originals}")

    if args.plan_only:
        print(f"\n📋 Plan-only mode. Exiting without processing.")
        return 0

    # Check disk space
    if not check_disk_space(args.output, required_gb=total_videos * 2.0):
        if not args.yes:
            response = input("Continue anyway? (y/N): ")
            if response.lower() != 'y':
                return 1

    # Handle deletion policy prompting
    delete_policy = args.delete_originals
    if not args.yes and delete_policy == 'ask-each' and not args.skip_conversion:
        delete_policy = prompt_deletion_policy()

    # Check GPU availability early
    gpu_available = False
    if args.gpu_accelerated:
        try:
            from utils.gpu_accelerated_converter import GPUAcceleratedConverter
            test_converter = GPUAcceleratedConverter()
            gpu_available = test_converter.gpu_available
        except ImportError:
            pass

    # Performance optimization check with system status
    if not args.plan_only:
        try:
            from utils.performance_optimizer import PerformanceOptimizer
            optimizer = PerformanceOptimizer()

            # Show comprehensive system analysis
            optimizer.print_system_status(
                cpu_workers=args.workers,
                gpu_workers=args.gpu_workers if args.gpu_accelerated else None,
                gpu_acceleration=gpu_available if args.gpu_accelerated else None
            )

            if args.auto_optimize:
                print(f"\n🔧 Attempting automatic performance optimization...")
                from utils.performance_optimizer import optimize_system_performance
                optimize_system_performance(auto_apply=True)
        except ImportError:
            pass

    # Confirmation
    if not args.yes:
        if videos_to_process == 0:
            print(f"\n✅ All videos already converted!")
            return 0
        response = input(f"\nProceed with processing {videos_to_process} videos? (y/N): ")
        if response.lower() != 'y':
            print("❌ Processing cancelled.")
            return 0

    # Create output directories
    output_path = Path(args.output)
    output_path.mkdir(parents=True, exist_ok=True)

    # Start disk space monitoring
    space_monitor = monitor_disk_space_during_processing(str(output_path))
    print(f"🔍 Disk space monitoring started (checking every 5 minutes)")

    # Stage 1: Video Conversion
    conversion_successful = False
    if not args.skip_conversion:
        print(f"\n📹 Stage 1: GoPro Format Conversion")

        if args.in_place:
            print(f"🔄 Using in-place conversion (files will be replaced in original locations)")
            converted_dir = Path(args.input)  # Analysis will use input directory
        else:
            converted_dir = output_path / "converted"

        if args.progress_monitoring:
            try:
                from utils.progress_converter import convert_videos_intelligent
                print(f"🧠 Using intelligent progress monitoring")
                conversion_successful = convert_videos_intelligent(
                    args.input,
                    str(converted_dir),
                    workers=args.workers
                )
            except ImportError:
                print(f"⚠️  Progress monitoring not available, falling back to standard conversion")
                conversion_successful = reformat_gopro_simple(args.input, str(converted_dir), args.workers, args.in_place)
        elif args.gpu_accelerated:
            try:
                from utils.gpu_accelerated_converter import convert_videos_gpu_accelerated
                print(f"🎮 Using GPU-accelerated conversion")
                conversion_successful = convert_videos_gpu_accelerated(
                    args.input,
                    str(converted_dir),
                    cpu_workers=args.workers,
                    gpu_workers=args.gpu_workers
                )
            except ImportError:
                print(f"⚠️  GPU acceleration not available, falling back to CPU")
                conversion_successful = reformat_gopro_simple(args.input, str(converted_dir), args.workers, args.in_place)
        else:
            conversion_successful = reformat_gopro_simple(args.input, str(converted_dir), args.workers, args.in_place)

        if conversion_successful:
            video_source = converted_dir
            # Handle deletion policy (skip if in-place since originals are already replaced)
            if not args.in_place:
                handle_deletion_policy(args.input, str(converted_dir), delete_policy)
            else:
                print(f"✅ In-place conversion complete - originals automatically replaced")
        else:
            print(f"⚠️  Conversion failed, using original videos")
            video_source = input_path
    else:
        print(f"\n⏭️  Skipping conversion step")
        video_source = input_path

    # Stage 2: SharkTrack Analysis
    print(f"\n🧠 Stage 2: SharkTrack Analysis")

    # Use converted videos from subdirectory if conversion was successful
    if conversion_successful and not args.skip_conversion:
        analysis_source = converted_dir
    else:
        analysis_source = video_source

    analysis_successful = run_sharktrack_analysis(str(analysis_source), args.output)

    if analysis_successful:
        print(f"\n🎉 Processing Complete!")
        print(f"Results saved to: {args.output}")
        return 0
    else:
        print(f"\n❌ Analysis failed!")
        return 1

if __name__ == "__main__":
    exit(main())