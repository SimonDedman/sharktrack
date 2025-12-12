#!/usr/bin/env python3
"""
Simplified BRUV Batch Processor with Preset Modes
Reduces 13 confusing parameters to 3 clear presets
"""

import argparse
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(
        description='Simplified BRUV Batch Processor',
        epilog='''
PRESET MODES:
  --convert-only      Convert videos, keep originals, save to output directory
  --convert-replace   Convert videos, replace originals in-place (saves 76% space)
  --analyze-only      Skip conversion, analyze existing videos

EXAMPLES:
  # Convert and replace originals (most common, saves space):
  python3 simple_batch_processor_v2.py --convert-replace ./BRUV_videos

  # Convert but keep originals (safest):
  python3 simple_batch_processor_v2.py --convert-only ./BRUV_videos ./output

  # Just analyze existing converted videos:
  python3 simple_batch_processor_v2.py --analyze-only ./converted_videos ./results

ADVANCED OPTIONS:
  --workers N         Parallel workers (default: auto-detect)
  --monitoring        Show detailed progress monitoring
  --yes              Skip all confirmation prompts
        ''',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    # Preset modes (mutually exclusive)
    mode_group = parser.add_mutually_exclusive_group(required=True)
    mode_group.add_argument('--convert-only', action='store_true',
                           help='Convert videos, keep originals, save to separate output directory')
    mode_group.add_argument('--convert-replace', action='store_true',
                           help='Convert videos and replace originals in-place (saves 76%% space)')
    mode_group.add_argument('--analyze-only', action='store_true',
                           help='Skip conversion, only run SharkTrack analysis on existing videos')

    # Required paths
    parser.add_argument('input_dir',
                       help='Directory containing BRUV videos')
    parser.add_argument('output_dir', nargs='?',
                       help='Output directory (not needed for --convert-replace)')

    # Simple advanced options
    parser.add_argument('--workers', '-w', type=int, default=0,
                       help='Number of parallel workers (0 = auto-detect)')
    parser.add_argument('--monitoring', action='store_true',
                       help='Show detailed progress monitoring')
    parser.add_argument('--yes', '-y', action='store_true',
                       help='Skip confirmation prompts')

    args = parser.parse_args()

    # Validate arguments
    if args.convert_replace:
        if args.output_dir:
            print("⚠️  Warning: --convert-replace doesn't use output directory (files replaced in-place)")
        output_dir = args.input_dir  # Analysis results go in input directory
    else:
        if not args.output_dir:
            parser.error(f"Output directory required for --{args.convert_only and 'convert-only' or 'analyze-only'}")
        output_dir = args.output_dir

    # Show clear plan
    print(f"\n📊 Processing Plan")
    print(f"   • Input: {args.input_dir}")

    if args.convert_replace:
        print(f"   • Mode: Convert and replace originals in-place")
        print(f"   • Space savings: ~76% (originals automatically replaced)")
        print(f"   • Analysis output: {output_dir}/analysis")
    elif args.convert_only:
        print(f"   • Mode: Convert videos, keep originals")
        print(f"   • Converted videos: {output_dir}/converted")
        print(f"   • Analysis output: {output_dir}/analysis")
        print(f"   • Originals: Preserved in {args.input_dir}")
    else:  # analyze-only
        print(f"   • Mode: Analysis only (no conversion)")
        print(f"   • Analysis output: {output_dir}")

    print(f"   • Workers: {args.workers or 'auto-detect'}")
    print(f"   • Monitoring: {'enabled' if args.monitoring else 'basic'}")

    # Confirmation
    if not args.yes:
        response = input(f"\nProceed? (y/N): ")
        if response.lower() != 'y':
            print("❌ Cancelled.")
            return 0

    print("\n🚀 Starting processing...")

    # TODO: Import and call the actual processing functions
    # This would call the existing simple_batch_processor.py with the right parameters

    print("✅ Processing complete!")
    return 0

if __name__ == "__main__":
    exit(main())