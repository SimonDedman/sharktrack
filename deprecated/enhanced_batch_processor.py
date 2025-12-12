#!/usr/bin/env python3
"""
Enhanced BRUV Batch Processor with Resumable Progress and Dynamic Load Balancing
Combines all advanced features: resumption, dynamic optimization, deletion policy
"""

import os
import argparse
import threading
from pathlib import Path
from typing import List
import time

from utils.resumable_processor import ResumableProcessor, resume_or_start_batch
from utils.dynamic_load_balancer import DynamicLoadBalancer
from simple_batch_processor import (
    reformat_gopro_simple, handle_deletion_policy,
    check_disk_space, prompt_deletion_policy
)

class EnhancedBRUVProcessor:
    """
    Advanced BRUV processor with resumption and dynamic optimization
    """

    def __init__(self,
                 batch_name: str,
                 input_dir: str,
                 output_dir: str,
                 initial_workers: int = 8,
                 delete_policy: str = "ask-each"):

        self.batch_name = batch_name
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.initial_workers = initial_workers
        self.delete_policy = delete_policy

        # Initialize resumable processor
        self.processor = ResumableProcessor(batch_name, input_dir, output_dir)

        # Initialize dynamic load balancer
        self.load_balancer = DynamicLoadBalancer(
            initial_workers=initial_workers,
            min_workers=max(1, initial_workers // 2),
            max_workers=initial_workers * 2,
            target_cpu_usage=85.0
        )

    def convert_single_video(self, task) -> dict:
        """
        Convert a single video with progress tracking
        """
        task_id = task.task_id
        input_path = task.input_path
        output_path = Path(task.output_path)

        try:
            # Mark task as started
            worker_id = threading.current_thread().name
            self.processor.mark_task_started(task_id, worker_id)

            # Check if output already exists
            if output_path.exists() and output_path.stat().st_size > 1024:
                print(f"   ⏭️  {Path(input_path).name} already converted, skipping")
                self.processor.mark_task_skipped(task_id, "Output already exists")
                return {'success': True, 'skipped': True}

            # Create output directory
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Convert video using ffmpeg
            print(f"   🔄 Converting {Path(input_path).name}")

            cmd = [
                'ffmpeg', '-i', input_path,
                '-c:v', 'libx264', '-preset', 'fast', '-crf', '23',
                '-c:a', 'aac', '-b:a', '128k',
                '-f', 'mp4', '-y', str(output_path)
            ]

            import subprocess
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)

            if result.returncode == 0 and output_path.exists():
                print(f"   ✅ {Path(input_path).name} converted successfully")
                self.processor.mark_task_completed(task_id, str(output_path))
                return {'success': True, 'output_path': str(output_path)}
            else:
                error_msg = f"FFmpeg failed: {result.stderr[:200]}..."
                print(f"   ❌ {Path(input_path).name} conversion failed")
                self.processor.mark_task_failed(task_id, error_msg)
                return {'success': False, 'error': error_msg}

        except subprocess.TimeoutExpired:
            error_msg = "Conversion timed out (>1 hour)"
            print(f"   ⏰ {Path(input_path).name} timed out")
            self.processor.mark_task_failed(task_id, error_msg)
            return {'success': False, 'error': error_msg}

        except Exception as e:
            error_msg = str(e)
            print(f"   ❌ {Path(input_path).name} failed: {error_msg}")
            self.processor.mark_task_failed(task_id, error_msg)
            return {'success': False, 'error': error_msg}

    def process_batch(self):
        """
        Process the complete batch with resumption and dynamic optimization
        """

        print(f"\n🚀 Enhanced BRUV Batch Processing")
        print(f"   • Input: {self.input_dir}")
        print(f"   • Output: {self.output_dir}")
        print(f"   • Workers: {self.initial_workers} (dynamic)")
        print(f"   • Delete policy: {self.delete_policy}")

        # Load or initialize batch
        if not self.processor.load_existing_progress():
            self.processor.initialize_new_batch(self.delete_policy)

        # Get pending tasks
        pending_tasks = self.processor.get_pending_tasks()
        failed_tasks = self.processor.get_failed_tasks()

        if not pending_tasks and not failed_tasks:
            print(f"\n✅ All tasks already completed!")
            self.processor.print_progress_summary()
            return

        # Combine pending and failed tasks for processing
        tasks_to_process = pending_tasks + failed_tasks
        print(f"\n📋 Tasks to process: {len(tasks_to_process)}")

        # Show current progress
        self.processor.print_progress_summary()

        # Stage 1: Video Conversion with Dynamic Load Balancing
        print(f"\n📹 Stage 1: Video Conversion (Dynamic Load Balancing)")

        start_time = time.time()

        try:
            # Start dynamic load balancing
            results = self.load_balancer.start_processing(
                self.convert_single_video,
                tasks_to_process
            )

            # Process results
            successful_conversions = sum(1 for r in results if r.get('success', False))
            failed_conversions = len(results) - successful_conversions

            conversion_time = time.time() - start_time

            print(f"\n✅ Conversion completed in {conversion_time/3600:.1f} hours")
            print(f"   • Successful: {successful_conversions}")
            print(f"   • Failed: {failed_conversions}")

            # Get load balancer performance report
            lb_report = self.load_balancer.get_performance_report()
            print(f"   • Average CPU usage: {lb_report.get('average_cpu_usage', 0):.1f}%")
            print(f"   • Average throughput: {lb_report.get('average_throughput', 0):.2f} videos/sec")
            print(f"   • Worker adjustments: {lb_report.get('worker_adjustments', 0)}")

            # Stage 2: Handle deletion policy
            if successful_conversions > 0:
                print(f"\n🗑️  Stage 2: Original Video Management")
                converted_dir = Path(self.output_dir) / "converted"
                deletion_success = handle_deletion_policy(
                    self.input_dir,
                    str(converted_dir),
                    self.delete_policy
                )

                if deletion_success:
                    print(f"✅ Original videos deleted successfully")
                else:
                    print(f"✅ Original videos retained")

            # Final progress summary
            print(f"\n🎉 Batch Processing Complete!")
            self.processor.print_progress_summary()

            # Cleanup progress files if everything completed
            remaining = self.processor.get_remaining_task_count()
            if remaining == 0:
                response = input(f"\nAll tasks completed. Clean up progress files? (Y/n): ")
                if response.lower() in ['', 'y', 'yes']:
                    self.processor.cleanup_progress_files()

        except KeyboardInterrupt:
            print(f"\n⚠️  Processing interrupted by user")
            print(f"Progress has been saved. Run again to resume from where you left off.")
            self.processor.save_progress()

        except Exception as e:
            print(f"\n❌ Processing failed: {e}")
            self.processor.save_progress()


def main():
    parser = argparse.ArgumentParser(description='Enhanced BRUV Batch Processor with Resumption')

    parser.add_argument('--input', '-i', required=True,
                       help='Input directory containing BRUV videos')
    parser.add_argument('--output', '-o', required=True,
                       help='Output directory for processed results')
    parser.add_argument('--batch-name', '-b', default="BRUV_Batch",
                       help='Name for this batch (used for progress tracking)')
    parser.add_argument('--workers', '-w', type=int, default=0,
                       help='Initial number of workers (0 = auto-detect)')
    parser.add_argument('--delete-originals', choices=['delete-all', 'ask-each', 'no'],
                       default='ask-each',
                       help='How to handle original videos after conversion')
    parser.add_argument('--resume', action='store_true',
                       help='Force attempt to resume existing batch')
    parser.add_argument('--fresh', action='store_true',
                       help='Force start fresh (ignore existing progress)')
    parser.add_argument('--status', action='store_true',
                       help='Show current batch status and exit')
    parser.add_argument('--yes', '-y', action='store_true',
                       help='Skip confirmation prompts')

    args = parser.parse_args()

    # Auto-detect workers if not specified
    if args.workers == 0:
        try:
            import multiprocessing
            import psutil
            cpu_cores = multiprocessing.cpu_count()
            memory_gb = psutil.virtual_memory().total / (1024**3)
            auto_workers = min(cpu_cores, int(memory_gb // 2), 12)
            auto_workers = max(1, auto_workers)
            args.workers = auto_workers
            print(f"🧠 Auto-detected {auto_workers} optimal workers")
        except ImportError:
            args.workers = 8
            print(f"⚠️  Using fallback: {args.workers} workers")

    # Status mode
    if args.status:
        processor = ResumableProcessor(args.batch_name, args.input, args.output)
        if processor.load_existing_progress():
            processor.print_progress_summary()
        else:
            print(f"❌ No existing batch found")
        return 0

    # Check input directory
    if not Path(args.input).exists():
        print(f"❌ Input directory does not exist: {args.input}")
        return 1

    # Check disk space
    if not check_disk_space(args.output, required_gb=100):
        if not args.yes:
            response = input("Continue anyway? (y/N): ")
            if response.lower() != 'y':
                return 1

    # Handle deletion policy prompting
    delete_policy = args.delete_originals
    if not args.yes and delete_policy == 'ask-each':
        delete_policy = prompt_deletion_policy()

    # Fresh start mode
    if args.fresh:
        processor = ResumableProcessor(args.batch_name, args.input, args.output)
        if processor.progress_file.exists():
            response = input(f"⚠️  Delete existing progress and start fresh? (y/N): ")
            if response.lower() == 'y':
                processor.cleanup_progress_files()
                print(f"🧹 Cleaned up existing progress")
            else:
                print(f"❌ Cancelled")
                return 1

    # Create and run enhanced processor
    try:
        enhanced_processor = EnhancedBRUVProcessor(
            batch_name=args.batch_name,
            input_dir=args.input,
            output_dir=args.output,
            initial_workers=args.workers,
            delete_policy=delete_policy
        )

        enhanced_processor.process_batch()
        return 0

    except Exception as e:
        print(f"❌ Failed to start processing: {e}")
        return 1


if __name__ == "__main__":
    exit(main())