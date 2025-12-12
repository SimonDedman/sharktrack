# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

SharkTrack is a machine learning-powered computer vision system for detecting and tracking sharks and rays (elasmobranchs) in Baited Remote Underwater Video Systems (BRUVS). It uses YOLO object detection with custom tracking to compute MaxN metrics 21x faster than traditional manual annotation methods.

### Key Capabilities
- Detects elasmobranchs in underwater videos with 89% accuracy
- Tracks individuals across frames to compute MaxN (maximum number of individuals seen simultaneously)
- Supports two modes: "peek" (fast keyframe detection) and "analyst" (full tracking with MaxN computation)
- Runs on standard laptops without advanced hardware requirements

## Architecture Overview

### Core Components

**Main Application (`app.py`)**
- Entry point with Click CLI interface
- `Model` class orchestrates the entire detection/tracking pipeline
- Supports two inference modes:
  - `keyframe_detection()`: Peek mode using PyAV for faster processing
  - `track_video()`: Full tracking mode using OpenCV with BoT-SORT tracker
- Handles video iteration, model inference, and result saving

**Detection Pipeline Flow**
1. Video preprocessing (optional GoPro reformatting via `utils/reformat_gopro.py`)
2. Frame extraction using stride (analyst mode) or keyframes (peek mode)
3. YOLO inference on extracted frames
4. Object tracking (analyst mode only) using BoT-SORT tracker
5. Post-processing and filtering of detections
6. Annotation image generation and CSV output

**Utilities Module (`utils/`)**
- `sharktrack_annotations.py`: Core annotation processing, tracking postprocessing, and output generation
- `video_iterators.py`: Two video iteration strategies (stride-based and keyframe-based)
- `compute_maxn.py`: Post-processing script to convert cleaned annotations to MaxN metrics
- `species_classifier.py`: Optional DenseNet-based species classification
- `time_processor.py`: Time format conversions (ms ↔ string)
- `path_resolver.py`: Path handling and output directory management
- `image_processor.py`: Frame extraction and annotation visualization

### Model Architecture
- **Object Detection**: YOLOv8 (`models/sharktrack.pt`) trained specifically for elasmobranch detection
- **Tracking**: BoT-SORT tracker configured in `trackers/tracker_3fps.yaml`
- **Species Classification**: Optional DenseNet121 classifier for species identification

## Development Commands

### Primary Commands
```bash
# Basic detection (analyst mode - full tracking)
python app.py --input ./input_videos --output ./output

# Peek mode (fast keyframe detection, no tracking)
python app.py --input ./input_videos --peek --output ./output

# Process with chapters (for split video files)
python app.py --input ./input_videos --chapters --output ./output

# Live tracking visualization (debugging)
python app.py --input ./single_video.mp4 --live --output ./debug_output

# Compute MaxN from cleaned annotations
python utils/compute_maxn.py --path ./output --videos ./input_videos

# Batch processing script for BRUV data
./process_bruv_data.sh
```

### Testing
```bash
# Run unit tests
python -m pytest tests/

# Test specific module
python -m pytest tests/test_compute_maxn.py
```

### Environment Setup
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
```

## Key Patterns and Conventions

### Video Processing Patterns
- **Dual Iterator Strategy**: `stride_iterator()` for precise tracking vs `keyframe_iterator()` for speed
- **Frame Skip Calculation**: Automatically adapts to video FPS to maintain consistent 3fps processing
- **Track Persistence**: Uses `persist=True` in YOLO tracking to maintain IDs across frames

### Data Flow Architecture
1. **Raw Detection**: YOLO generates bounding boxes with confidence scores
2. **Track Assignment**: BoT-SORT assigns consistent IDs across frames
3. **Post-processing**: Filter false positives based on track length, motion, and confidence
4. **Annotation**: Generate max-confidence detection images for manual review
5. **Classification**: Optional automated species classification
6. **MaxN Computation**: Aggregate cleaned annotations into MaxN metrics

### Output Structure Pattern
```
output/
├── internal_results/
│   ├── output.csv              # All detections with tracking info
│   ├── overview.csv            # Per-video summary
│   └── videos/
│       └── {video_name}/
│           └── {track_id}.jpg  # Max-confidence detection per track
└── analysed/
    ├── maxn.csv                # Final MaxN metrics
    └── videos/
        └── {video_name}/
            └── {species}.jpg   # MaxN visualization frames
```

### Configuration Management
- **Tracker Config**: YAML files in `trackers/` define BoT-SORT parameters
- **Detection Thresholds**: Configurable confidence, IoU, and motion thresholds
- **Species Mapping**: Hard-coded to single "elasmobranch" class with optional fine-grained classification

## Critical Implementation Details

### PyTorch Compatibility Fix
- Patches `torch.load()` to handle PyTorch 2.6+ `weights_only` parameter changes
- Essential for model loading compatibility across PyTorch versions

### Video Format Handling
- GoPro videos require reformatting due to audio codec issues
- `utils/reformat_gopro.py` handles MP4 container fixes
- Uses FFmpeg under the hood for format conversion

### Track Post-processing Logic
Key filtering criteria in `postprocess()`:
- **Length Threshold**: Tracks must persist for at least `fps` frames (1 second)
- **Motion Threshold**: Minimum 8% movement relative to frame size
- **Confidence Threshold**: 70% confidence required for short/static tracks
- **False Positive Detection**: Combines length, motion, and confidence criteria

### Memory and Performance
- Processes videos frame-by-frame to avoid memory issues with large files
- Uses generator patterns for video iteration
- Automatic device selection (CUDA vs CPU)
- Configurable image size for speed/accuracy tradeoff

## Species Classification Integration
- Optional DenseNet121-based classifier can be plugged in via `--species_classifier` flag
# - Requires separate model files: `classifier.pt` and `class_mapping.txt`
- Automatic confidence thresholding (45%) with fallback to manual classification

## Workflow Integration Points

### Resume Functionality
- Tracks processed videos in `overview.csv` to enable interrupted run resumption
- Maintains global track ID counter across sessions
- Useful for large datasets processed over multiple sessions

### Manual Annotation Workflow
1. Run SharkTrack in analyst mode
2. Review detection images in `internal_results/videos/`
3. Delete false positives, rename with species: `{track_id}-{species}.jpg`
4. Run `compute_maxn.py` to generate final MaxN metrics

### Batch Processing
- `process_bruv_data.sh` provides template for processing multiple video files
- Creates temporary hardlinks to avoid data duplication
- Handles reformatting and processing in sequence

## Dependencies and Environment

### Core Dependencies
- **ultralytics**: YOLOv8 implementation
- **torch/torchvision**: Deep learning framework
- **opencv-python**: Video processing and computer vision
- **av**: Fast video codec access (for peek mode)
- **pandas**: Data manipulation and CSV handling
- **numpy**: Numerical computations (constrained to <2.0 for compatibility)

### Hardware Considerations
- CUDA support automatically detected and utilized when available
- Fallback to CPU processing for systems without GPU
- Memory usage scales with video resolution and batch size

## Strategic Delivery Framework

### Project Management Philosophy

When processing large BRUV datasets, balance immediate delivery requirements with strategic platform development opportunities. This approach treats the current video processing requirement as both a deliverable and a foundation for potential gamechanging research tools.

### Three-Phase Development Strategy

#### Phase 1: DELIVERY FIRST (Week 1-2)
**Priority: Get videos processed reliably**

**Immediate Actions:**
- Ship the working progress converter for reliable video processing
- Process the complete BRUV dataset using stable tools
- Document the workflow for reproducibility
- Deliver on core requirement - don't let perfect be the enemy of good

**Risk Management:**
- Keep enhanced features optional (e.g., `--progress-monitoring` flag)
- Maintain fallback to simple batch processor
- Focus on reliability over features

#### Phase 2: LEARN WHILE DELIVERING (Weeks 2-4)
**Priority: Extract insights during processing**

**During video processing:**
- Document pain points - what breaks, what's slow, what's confusing
- Measure performance - actual throughput, error rates, user experience
- Collect metadata - what environmental data is available vs missing
- Note research workflow - how marine biologists actually work with this data

**Strategic Questions to Answer:**
1. What metadata is consistently available vs wishful thinking?
2. Which detection confidence thresholds work best in practice?
3. What environmental factors most affect detection accuracy?
4. How do researchers actually review and annotate results?

#### Phase 3: PLATFORM FOUNDATION (Weeks 3-6)
**Priority: Build for scale while delivering**

**Technical Foundation:**
- Database schema - start logging all processing results properly
- API-first approach - make components reusable
- Standard data formats - ensure outputs work with existing research tools
- Monitoring infrastructure - track system performance and usage

**Research Integration:**
- Partner with 2-3 research groups for validation
- Standardise metadata collection across different BRUV deployments
- Test annotation workflows with actual marine biologists

### Strategic Advantages

**Risk Mitigation:**
- Primary deliverable protected - videos get processed regardless
- Learning happens in parallel, not blocking delivery
- Real-world testing with actual research data

**Competitive Intelligence:**
- Understand the marine research market better than any competitor
- Direct feedback from end users during development
- Proof of concept with real research outcomes

**Platform Credibility:**
- Built by someone who actually processed thousands of hours of BRUV footage
- Tested on real research data, not toy datasets
- Addresses actual pain points, not theoretical ones

### Success Metrics by Phase

**Phase 1 Success:**
- All BRUV videos processed successfully
- Results delivered to research team
- Stable, reproducible workflow documented

**Phase 2 Success:**
- 5+ pain points identified and documented
- Performance baseline established
- User workflow mapped and validated

**Phase 3 Success:**
- 2+ research groups actively using the system
- Standardised data pipeline operational
- Clear product-market fit evidence

### Resource Allocation Guidelines

**Time Split:**
- 60% Core delivery (video processing)
- 25% Learning and documentation
- 15% Platform experimentation

**Decision Points:**
- After Phase 1: If processing succeeds → continue; if major issues → focus purely on delivery
- After Phase 2: If research adoption high → invest in platform; if lukewarm → deliver and document
- After Phase 3: Strong adoption → pursue funding; moderate → open source; weak → learning experience

This framework ensures the immediate research requirements are met while maximising the strategic value of the development work for potential future platform opportunities.