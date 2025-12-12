#!/usr/bin/env python3
"""
Comprehensive BRUV Data Processing Pipeline
Handles GoPro reformatting, SharkTrack analysis, and metadata extraction for entire datasets
"""

import os
import sys
import argparse
from pathlib import Path
from datetime import datetime
import subprocess
import json

# Add current directory to path to import our modules
sys.path.append(str(Path(__file__).parent))

from utils.batch_processor import BatchProcessingConfig, EnhancedBatchProcessor
from utils.auto_populator import MetadataAutoPopulator
from utils.reformat_gopro import main as reformat_gopro


def get_storage_info(path: str) -> dict:
    """Get storage information for a given path"""
    statvfs = os.statvfs(path)

    # Calculate sizes in GB
    total_space = (statvfs.f_frsize * statvfs.f_blocks) / (1024**3)
    free_space = (statvfs.f_frsize * statvfs.f_bavail) / (1024**3)
    used_space = total_space - free_space

    return {
        'total_gb': total_space,
        'free_gb': free_space,
        'used_gb': used_space,
        'free_percent': (free_space / total_space) * 100
    }


def estimate_storage_requirements(input_dir: str) -> dict:
    """Estimate storage requirements for processing"""
    input_path = Path(input_dir)

    # Find all video files and calculate total size
    total_size = 0
    video_count = 0

    for ext in ['.mp4', '.MP4', '.avi', '.AVI', '.mov', '.MOV']:
        for video_file in input_path.rglob(f'*{ext}'):
            try:
                total_size += video_file.stat().st_size
                video_count += 1
            except (OSError, PermissionError):
                continue

    total_size_gb = total_size / (1024**3)

    # Estimate storage needs
    # - Converted videos: ~same size as originals (copying video stream)
    # - Analysis outputs: ~1-5% of video size (images, CSVs, metadata)
    # - Temporary space: ~10% for processing

    converted_size_gb = total_size_gb  # GoPro conversion (copy video stream)
    analysis_size_gb = total_size_gb * 0.05  # Analysis outputs (~5%)
    temp_space_gb = total_size_gb * 0.1  # Temporary processing space

    total_required_gb = converted_size_gb + analysis_size_gb + temp_space_gb

    return {
        'input_size_gb': total_size_gb,
        'video_count': video_count,
        'converted_size_gb': converted_size_gb,
        'analysis_size_gb': analysis_size_gb,
        'temp_space_gb': temp_space_gb,
        'total_required_gb': total_required_gb,
        'safety_margin_gb': total_required_gb * 1.2  # 20% safety margin
    }


def check_storage_safety(input_dir: str, output_dir: str) -> bool:
    """Check if there's sufficient storage space"""
    print("💾 Checking storage requirements...")

    # Get storage requirements
    requirements = estimate_storage_requirements(input_dir)

    # Get available storage on output device
    output_storage = get_storage_info(output_dir)

    print(f"\n📊 Storage Analysis:")
    print(f"   • Input videos: {requirements['input_size_gb']:.1f} GB ({requirements['video_count']} files)")
    print(f"   • Converted videos: {requirements['converted_size_gb']:.1f} GB")
    print(f"   • Analysis outputs: {requirements['analysis_size_gb']:.1f} GB")
    print(f"   • Temporary space: {requirements['temp_space_gb']:.1f} GB")
    print(f"   • Total required: {requirements['total_required_gb']:.1f} GB")
    print(f"   • With safety margin: {requirements['safety_margin_gb']:.1f} GB")

    print(f"\n💽 Output Drive Status:")
    print(f"   • Total space: {output_storage['total_gb']:.1f} GB")
    print(f"   • Used space: {output_storage['used_gb']:.1f} GB")
    print(f"   • Free space: {output_storage['free_gb']:.1f} GB")
    print(f"   • Free percentage: {output_storage['free_percent']:.1f}%")

    # Safety checks
    if output_storage['free_gb'] < requirements['safety_margin_gb']:
        print(f"\n❌ INSUFFICIENT STORAGE!")
        print(f"   Required: {requirements['safety_margin_gb']:.1f} GB")
        print(f"   Available: {output_storage['free_gb']:.1f} GB")
        print(f"   Shortfall: {requirements['safety_margin_gb'] - output_storage['free_gb']:.1f} GB")
        return False

    if output_storage['free_percent'] < 10:
        print(f"\n⚠️  WARNING: Output drive is {output_storage['free_percent']:.1f}% full")
        print(f"   Consider using a different output location")

    print(f"\n✅ Sufficient storage available")
    return True


def check_prerequisites(input_dir: str = None, output_dir: str = None):
    """Check that all required dependencies are available"""
    print("🔍 Checking prerequisites...")

    # Check ffmpeg
    try:
        result = subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True)
        if result.returncode != 0:
            print("❌ ffmpeg not found. Please install ffmpeg.")
            return False
        print("✅ ffmpeg available")
    except FileNotFoundError:
        print("❌ ffmpeg not found. Please install ffmpeg.")
        return False

    # Check virtual environment
    if not os.path.exists('venv'):
        print("❌ Virtual environment not found. Please run: python3 -m venv venv")
        return False
    print("✅ Virtual environment available")

    # Check SharkTrack model
    model_path = Path("models/sharktrack.pt")
    if not model_path.exists():
        print("❌ SharkTrack model not found at models/sharktrack.pt")
        return False
    print("✅ SharkTrack model available")

    # Check storage if paths provided
    if input_dir and output_dir:
        if not check_storage_safety(input_dir, output_dir):
            return False

    return True


def estimate_processing_time(video_count: int, avg_duration_minutes: float = 60) -> dict:
    """Estimate processing time based on video count"""

    # Time estimates (minutes per video)
    reformat_time_per_video = 2  # GoPro reformatting
    sharktrack_time_per_video = avg_duration_minutes * 0.02  # 2% of video duration
    metadata_time_per_video = 0.5  # Metadata extraction

    total_per_video = reformat_time_per_video + sharktrack_time_per_video + metadata_time_per_video

    estimates = {
        'reformat_hours': (video_count * reformat_time_per_video) / 60,
        'sharktrack_hours': (video_count * sharktrack_time_per_video) / 60,
        'metadata_hours': (video_count * metadata_time_per_video) / 60,
        'total_hours': (video_count * total_per_video) / 60,
        'videos_per_hour': 60 / total_per_video if total_per_video > 0 else 0
    }

    return estimates


def create_processing_plan(input_directory: str, output_directory: str) -> dict:
    """Create a processing plan for the entire dataset"""

    input_path = Path(input_directory)
    output_path = Path(output_directory)

    # Find all video files
    video_files = []
    for ext in ['.mp4', '.MP4', '.avi', '.AVI', '.mov', '.MOV']:
        video_files.extend(list(input_path.rglob(f'*{ext}')))

    # Group by deployment (assuming BRUV folder structure)
    deployments = {}
    for video_file in video_files:
        # Try to extract deployment from path
        parts = video_file.parts
        deployment_id = None

        # Look for BRUV folder pattern
        for i, part in enumerate(parts):
            if 'BRUV' in part and i < len(parts) - 1:
                deployment_id = f"{parts[i]}_{parts[i+1] if i+1 < len(parts) else 'unknown'}"
                break

        if not deployment_id:
            deployment_id = video_file.parent.name

        if deployment_id not in deployments:
            deployments[deployment_id] = []
        deployments[deployment_id].append(video_file)

    # Calculate estimates
    total_videos = len(video_files)
    estimates = estimate_processing_time(total_videos)

    plan = {
        'input_directory': str(input_path),
        'output_directory': str(output_path),
        'total_videos': total_videos,
        'deployments': {k: len(v) for k, v in deployments.items()},
        'time_estimates': estimates,
        'processing_stages': [
            'GoPro format conversion (if needed)',
            'SharkTrack elasmobranch detection',
            'Metadata extraction and analysis',
            'Substrate classification',
            'Report generation'
        ]
    }

    return plan


def print_processing_plan(plan: dict):
    """Print a comprehensive processing plan"""
    print("\n" + "="*80)
    print("🌊 BRUV DATA PROCESSING PLAN")
    print("="*80)

    print(f"\n📁 Input Directory: {plan['input_directory']}")
    print(f"📁 Output Directory: {plan['output_directory']}")
    print(f"\n📊 Dataset Overview:")
    print(f"   • Total Videos: {plan['total_videos']}")
    print(f"   • Deployments: {len(plan['deployments'])}")

    print(f"\n⏱️  Time Estimates:")
    estimates = plan['time_estimates']
    print(f"   • GoPro Reformatting: {estimates['reformat_hours']:.1f} hours")
    print(f"   • SharkTrack Analysis: {estimates['sharktrack_hours']:.1f} hours")
    print(f"   • Metadata Processing: {estimates['metadata_hours']:.1f} hours")
    print(f"   • Total Estimated Time: {estimates['total_hours']:.1f} hours")
    print(f"   • Processing Rate: {estimates['videos_per_hour']:.1f} videos/hour")

    print(f"\n🔄 Processing Stages:")
    for i, stage in enumerate(plan['processing_stages'], 1):
        print(f"   {i}. {stage}")

    print(f"\n📋 Deployments Found:")
    for deployment, count in plan['deployments'].items():
        print(f"   • {deployment}: {count} videos")

    print("\n" + "="*80)


def prompt_deletion_policy() -> str:
    """Prompt user for deletion policy at start of processing"""
    print(f"\n🗑️  Original Video Deletion Policy")
    print(f"After successful GoPro format conversion, what should happen to original videos?")
    print(f"\nOptions:")
    print(f"   1. Delete all successfully converted originals (saves most space)")
    print(f"   2. Ask before deleting each batch (default)")
    print(f"   3. Keep all original videos (safest)")

    while True:
        choice = input(f"\nChoose deletion policy (1-3): ").strip()
        if choice == '1':
            print(f"✅ Will delete all successfully converted original videos")
            return 'delete-all'
        elif choice == '2':
            print(f"✅ Will ask before deleting each batch")
            return 'ask-each'
        elif choice == '3':
            print(f"✅ Will keep all original videos")
            return 'no'
        else:
            print(f"Invalid choice. Please enter 1, 2, or 3.")


def delete_original_videos(input_dir: str, converted_dir: str, policy: str) -> bool:
    """Delete original videos based on policy"""
    input_path = Path(input_dir)
    converted_path = Path(converted_dir)

    # Check conversion success
    original_videos = list(input_path.rglob('*.MP4')) + list(input_path.rglob('*.mp4'))
    converted_videos = list(converted_path.rglob('*.MP4')) + list(converted_path.rglob('*.mp4'))

    if len(converted_videos) == 0:
        print(f"⚠️  No converted videos found - keeping originals")
        return False

    # Calculate space savings
    original_size = sum(f.stat().st_size for f in original_videos if f.exists()) / (1024**3)

    if policy == 'no':
        print(f"✅ Keeping all original videos ({original_size:.1f} GB)")
        return False

    elif policy == 'delete-all':
        print(f"\n🗑️  Deleting original videos ({original_size:.1f} GB)...")
        deleted_count = 0
        for video_file in original_videos:
            try:
                video_file.unlink()
                deleted_count += 1
            except Exception as e:
                print(f"   Failed to delete {video_file}: {e}")
        print(f"✅ Deleted {deleted_count}/{len(original_videos)} original videos")
        return True

    elif policy == 'ask-each':
        print(f"\n🗑️  Original Video Cleanup")
        print(f"   • Original videos: {len(original_videos)} files ({original_size:.1f} GB)")
        print(f"   • Converted videos: {len(converted_videos)} files")

        if len(converted_videos) < len(original_videos):
            print(f"   ⚠️  Warning: {len(original_videos) - len(converted_videos)} videos failed to convert")

        confirm = input(f"\nDelete {len(original_videos)} original videos to save {original_size:.1f} GB? (y/N): ")

        if confirm.lower() in ['y', 'yes']:
            print(f"🗑️  Deleting original videos...")
            deleted_count = 0
            for video_file in original_videos:
                try:
                    video_file.unlink()
                    deleted_count += 1
                except Exception as e:
                    print(f"   Failed to delete {video_file}: {e}")
            print(f"✅ Deleted {deleted_count}/{len(original_videos)} original videos")
            return True
        else:
            print(f"✅ Keeping original videos")
            return False

    return False


def process_deployment_batch(input_dir: str, output_dir: str, skip_conversion: bool = False,
                           max_workers: int = 4, species_classifier: str = None,
                           delete_originals_policy: str = 'ask-each'):
    """Process a complete BRUV dataset"""

    input_path = Path(input_dir)
    output_path = Path(output_dir)

    print(f"\n🚀 Starting BRUV dataset processing...")
    print(f"Input: {input_path}")
    print(f"Output: {output_path}")

    # Create output directory structure
    output_path.mkdir(parents=True, exist_ok=True)
    converted_path = output_path / "converted"
    analysis_path = output_path / "analysis"
    reports_path = output_path / "reports"

    # Stage 1: GoPro Format Conversion
    conversion_successful = False
    if not skip_conversion:
        print(f"\n📹 Stage 1: GoPro Format Conversion")
        print(f"Converting videos to standard format...")

        try:
            reformat_gopro(str(input_path), str(converted_path), None)
            print(f"✅ GoPro conversion completed")
            video_source = converted_path
            conversion_successful = True
        except Exception as e:
            print(f"⚠️  GoPro conversion failed: {e}")
            print(f"Proceeding with original videos...")
            video_source = input_path
    else:
        print(f"\n⏭️  Skipping GoPro conversion (--skip-conversion specified)")
        video_source = input_path

    # Handle original video deletion based on policy
    if conversion_successful:
        delete_original_videos(str(input_path), str(converted_path), delete_originals_policy)

    # Stage 2: Enhanced Metadata and SharkTrack Analysis
    print(f"\n🧠 Stage 2: Enhanced Analysis Pipeline")

    # Configure batch processing
    config = BatchProcessingConfig(
        input_directory=str(video_source),
        output_directory=str(analysis_path),
        metadata_template="templates/deployment_metadata_template.md",
        species_classifier_path=species_classifier,
        max_workers=max_workers,
        recursive_search=True,
        enable_substrate_classification=True,
        enable_database_lookup=True,
        enable_metadata_export=True,
        create_summary_report=True
    )

    # Run batch processing
    processor = EnhancedBatchProcessor(config)
    results = processor.process_batch()

    # Stage 3: Generate Final Reports
    print(f"\n📊 Stage 3: Final Report Generation")
    generate_final_reports(results, reports_path, input_path)

    print(f"\n🎉 Processing Complete!")
    print(f"Results saved to: {output_path}")
    print(f"Analysis data: {analysis_path}")
    print(f"Reports: {reports_path}")

    return results


def generate_final_reports(results, reports_path: Path, input_path: Path):
    """Generate comprehensive final reports"""
    reports_path.mkdir(parents=True, exist_ok=True)

    # Processing summary
    summary = {
        'processing_date': datetime.now().isoformat(),
        'input_directory': str(input_path),
        'total_videos': results.total_videos,
        'successful_analyses': results.successful,
        'failed_analyses': results.failed,
        'processing_time_hours': results.processing_time / 3600,
        'success_rate': (results.successful / results.total_videos) * 100 if results.total_videos > 0 else 0
    }

    # Save summary
    with open(reports_path / "processing_summary.json", 'w') as f:
        json.dump(summary, f, indent=2)

    # Create markdown summary
    summary_md = f"""# BRUV Dataset Processing Summary

**Processing Date**: {summary['processing_date']}
**Input Directory**: {summary['input_directory']}

## Results Overview
- **Total Videos**: {summary['total_videos']}
- **Successful Analyses**: {summary['successful_analyses']}
- **Failed Analyses**: {summary['failed_analyses']}
- **Success Rate**: {summary['success_rate']:.1f}%
- **Processing Time**: {summary['processing_time_hours']:.2f} hours

## Outputs Generated
- Individual video analysis results
- Substrate classification maps
- Species detection summaries
- Metadata extraction reports
- Batch processing statistics

*Generated by Enhanced SharkTrack System*
"""

    with open(reports_path / "processing_summary.md", 'w') as f:
        f.write(summary_md)

    print(f"✅ Reports generated in: {reports_path}")


def main():
    """Main processing function"""
    parser = argparse.ArgumentParser(description='Process complete BRUV datasets with SharkTrack')

    parser.add_argument('--input', '-i', required=True,
                       help='Input directory containing BRUV videos')
    parser.add_argument('--output', '-o', required=True,
                       help='Output directory for processed results')
    parser.add_argument('--workers', '-w', type=int, default=4,
                       help='Number of parallel workers (default: 4)')
    parser.add_argument('--skip-conversion', action='store_true',
                       help='Skip GoPro format conversion step')
    parser.add_argument('--species-classifier', '-sc', type=str,
                       help='Path to species classifier model directory')
    parser.add_argument('--plan-only', action='store_true',
                       help='Show processing plan without executing')
    parser.add_argument('--yes', '-y', action='store_true',
                       help='Skip confirmation prompts')
    parser.add_argument('--delete-originals', choices=['delete-all', 'ask-each', 'no'],
                       default='ask-each',
                       help='How to handle original videos after conversion (default: ask-each)')

    args = parser.parse_args()

    # Check prerequisites including storage
    if not check_prerequisites(args.input, args.output):
        print("\n❌ Prerequisites not met. Please fix the issues above.")
        return 1

    # Validate paths
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"❌ Input directory does not exist: {input_path}")
        return 1

    # Create processing plan
    plan = create_processing_plan(args.input, args.output)
    print_processing_plan(plan)

    if args.plan_only:
        print("\n📋 Plan-only mode. Exiting without processing.")
        return 0

    # Handle deletion policy prompting if using default
    delete_policy = args.delete_originals
    if not args.yes and delete_policy == 'ask-each' and not args.skip_conversion:
        # Prompt user for deletion policy upfront to avoid babysitting
        delete_policy = prompt_deletion_policy()

    # Confirmation
    if not args.yes:
        response = input(f"\nProceed with processing {plan['total_videos']} videos? (y/N): ")
        if response.lower() != 'y':
            print("❌ Processing cancelled.")
            return 0

    # Process the dataset
    try:
        results = process_deployment_batch(
            input_dir=args.input,
            output_dir=args.output,
            skip_conversion=args.skip_conversion,
            max_workers=args.workers,
            species_classifier=args.species_classifier,
            delete_originals_policy=delete_policy
        )

        print(f"\n✅ Successfully processed {results.successful}/{results.total_videos} videos")
        return 0

    except KeyboardInterrupt:
        print(f"\n⚠️  Processing interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Processing failed: {e}")
        return 1


if __name__ == "__main__":
    exit(main())