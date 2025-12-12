# SharkTrack Setup and Usage Guide

*Updated: September 2025*

## System Overview

SharkTrack is a marine research platform for automated fish detection and tracking in BRUV (Baited Remote Underwater Video) footage. The system combines video processing, machine learning analysis, and data consolidation for marine biodiversity research.

## Prerequisites

- **Python 3.13+** with virtual environment support
- **FFmpeg** for video processing
- **CUDA-capable GPU** (optional, for faster processing)
- **Minimum 4GB RAM per analysis worker**
- **Large storage capacity** for video files

## Installation

### 1. Virtual Environment Setup

```bash
cd /path/to/sharktrack-1.5/
python3 -m venv sharktrack-env
source sharktrack-env/bin/activate
pip install -r requirements.txt
```

### 2. Model Files

Ensure the following model files are present:
- `models/sharktrack.pt` (6.2MB YOLO detection model)
- `models/classifier.pt` (species classification - optional)
- `models/class_mapping.txt` (species mapping - optional)

## Core Workflows

### Video Conversion Workflow

SharkTrack uses efficient H.264 conversion to reduce file sizes while maintaining analysis quality.

#### Simple Batch Processor (Recommended)

```bash
source sharktrack-env/bin/activate

# Convert videos in-place (replaces originals)
python3 simple_batch_processor_v2.py /path/to/videos --convert-replace

# Convert only (keeps originals separate)
python3 simple_batch_processor_v2.py /path/to/videos --convert-only

# Analysis only (on already converted videos)
python3 simple_batch_processor_v2.py /path/to/videos --analyze-only
```

#### Advanced Batch Processor

```bash
# Full conversion + analysis pipeline
python3 batch_processor.py /path/to/videos /path/to/output --workers 4

# Convert only with custom settings
python3 batch_processor.py /path/to/videos /path/to/output --convert-only --workers 8 --delete-originals
```

### Analysis Workflow

#### Parallel Analysis (Production)

```bash
source sharktrack-env/bin/activate

# Auto-detected workers (recommended)
python3 parallel_sharktrack_analysis.py "/path/to/converted/videos" "/path/to/output"

# Custom worker count
python3 parallel_sharktrack_analysis.py "/path/to/videos" "/path/to/output" --workers 6

# Fast peek mode (keyframe detection only)
python3 parallel_sharktrack_analysis.py "/path/to/videos" "/path/to/output" --peek
```

#### Single Video Analysis

```bash
source sharktrack-env/bin/activate
echo "n" | python3 app.py --input "/path/to/video.MP4" --output "./results"
```

## File Organization

### Recommended Directory Structure

```
BRUV_Collection/
├── BRUV 46/
│   ├── GH012490.MP4                # Converted video (replaces original)
│   ├── GH012490.MP4.original       # Original backup
│   ├── GH022490.MP4
│   ├── GH022490.MP4.original
│   └── analysis_results/           # Analysis results co-located
│       ├── GH012490/
│       │   └── internal_results/
│       │       ├── output.csv      # Detection data
│       │       └── overview.csv    # Summary stats
│       └── GH022490/
│           └── internal_results/
├── BRUV 47/
│   ├── [similar structure]
└── consolidated/                   # Cross-deployment analysis
    ├── output.csv                  # All detections combined
    ├── overview.csv                # Per-video summaries
    ├── detection_images/           # Visual proof organized by video
    └── summary_report.txt          # Comprehensive analysis report
```

### Analysis Output Structure

Each analyzed video produces:
- **`output.csv`**: Detection coordinates, timestamps, confidence scores
- **`overview.csv`**: Per-video summary with track counts
- **`videos/*/track_*.jpg`**: Detection images for visual verification
- **Processing metadata**: Timing and performance statistics

## Worker Auto-Detection

The system automatically detects optimal worker counts based on:
- **CPU cores**: Physical + logical cores
- **Available RAM**: 4GB minimum per ML analysis worker
- **System load**: Adjusts for other running processes

**Conversion workers**: `min(CPU_cores, RAM_GB // 2, 16)`
**Analysis workers**: `min(CPU_cores, RAM_GB // 4, 8)`

## Performance Optimization

### Video Conversion
- **Parallel processing**: 4-16 workers depending on system
- **Intelligent progress monitoring**: Size-weighted ETA calculations
- **Space savings**: ~76% reduction (3.8GB → 7.7MB typical)
- **Quality preservation**: Optimized H.264 settings for analysis

### ML Analysis
- **Parallel subprocess isolation**: Prevents memory conflicts
- **Auto-balancing**: Optimal worker assignment
- **Comprehensive consolidation**: Combines results from all workers
- **Error recovery**: Individual video failures don't stop batch

### Storage Management
- **In-place conversion**: Saves storage with `--convert-replace`
- **Automatic cleanup**: Removes temporary worker directories
- **Backup creation**: Preserves originals as `.original` files

## Troubleshooting

### Common Issues

#### Virtual Environment Not Activated
```bash
# Always activate before running
source sharktrack-env/bin/activate
```

#### Dependencies Missing
```bash
# Reinstall requirements
pip install -r requirements.txt

# Check specific package
python3 -c "import pandas; print('OK')"
```

#### Read-only Filesystem
```bash
# Remount drive
sudo umount "/path/to/drive"
sudo mount "/path/to/drive"
```

#### Workers Hanging
- Check available RAM (4GB per analysis worker minimum)
- Reduce worker count: `--workers 2`
- Use peek mode for faster processing: `--peek`

#### Video Processing Fails
- Verify FFmpeg installation: `ffmpeg -version`
- Check video file integrity
- Ensure sufficient disk space

### Performance Tuning

#### For Analysis-Heavy Workloads
```bash
# Reduce workers to prevent memory exhaustion
python3 parallel_sharktrack_analysis.py "/path/to/videos" "/path/to/output" --workers 4

# Use peek mode for faster results
python3 parallel_sharktrack_analysis.py "/path/to/videos" "/path/to/output" --peek
```

#### For Storage-Constrained Systems
```bash
# Convert and delete originals immediately
python3 simple_batch_processor_v2.py /path/to/videos --convert-replace
```

## Data Management

### Backup Strategy
- **Original files**: Automatically backed up as `.original` during conversion
- **Analysis results**: Saved in original video directories for data locality
- **Consolidated reports**: Centralized summaries for cross-deployment analysis

### Quality Assurance
- **Detection images**: Visual verification of all tracked objects
- **Processing statistics**: Performance metrics per video
- **Error logging**: Comprehensive failure reporting

### Research Deliverables
- **Combined CSV files**: All detections across deployments
- **Summary reports**: Statistics and track counts
- **Visual evidence**: Organized detection images
- **Performance metrics**: Processing time and throughput data

## Advanced Configuration

### Custom Analysis Parameters
```bash
# Custom confidence threshold
python3 app.py --input video.MP4 --output results --conf 0.15

# Custom image size for processing
python3 app.py --input video.MP4 --output results --imgsz 1280
```

### Integration with External Systems
- Results are saved as standard CSV files for import into R, Python, MATLAB
- Detection images use standard JPEG format
- Summary reports use markdown-compatible text format

## Next Steps

This setup provides the foundation for:
1. **Marine biodiversity research**: Automated species detection and counting
2. **Long-term monitoring**: Consistent processing across multiple deployments
3. **Collaborative research**: Standardized output formats for data sharing
4. **Quality validation**: Visual verification and statistical summaries

For deployment-specific configurations and advanced features, see the other documentation files in the `docs/` directory.