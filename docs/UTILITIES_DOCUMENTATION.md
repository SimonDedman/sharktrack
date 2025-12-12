# SharkTrack Utilities Documentation

This document provides comprehensive documentation for all lower-level scripts and utilities in the SharkTrack codebase.

## Core Processing Architecture

### Current Production Setup (September 2025)

**Virtual Environment**: All commands require activation of the virtual environment
```bash
source sharktrack-env/bin/activate
```

**Dependencies**: Fully installed including pandas, torch, ultralytics, opencv
**Model Files**: `models/sharktrack.pt` (6.2MB) operational

### Parallel Analysis System (Production)

#### `parallel_sharktrack_analysis.py` - Production Parallel Processing

**Purpose**: High-performance parallel analysis with auto-balancing workers

**Features**:
- **Auto-detected workers**: Based on CPU cores and RAM (4GB per worker)
- **Subprocess isolation**: Prevents memory conflicts between workers
- **Progress monitoring**: Real-time status and ETA calculations
- **Result consolidation**: Combines outputs from all workers
- **Error recovery**: Individual failures don't stop batch processing

**Command Line Interface**:
```bash
# Auto-detected workers (recommended)
python3 parallel_sharktrack_analysis.py "/path/to/videos" "/path/to/output"

# Custom worker count
python3 parallel_sharktrack_analysis.py "/path/to/videos" "/path/to/output" --workers 6

# Fast peek mode
python3 parallel_sharktrack_analysis.py "/path/to/videos" "/path/to/output" --peek
```

**Performance**: 7 workers auto-detected (CPU: 12, RAM: 30.2GB), ~60s per video

#### `simple_batch_processor_v2.py` - Simplified Batch Processing

**Purpose**: User-friendly interface with 3 clear presets

**Presets**:
```bash
# Convert videos in-place (replaces originals)
python3 simple_batch_processor_v2.py /path/to/videos --convert-replace

# Convert only (keeps originals separate)
python3 simple_batch_processor_v2.py /path/to/videos --convert-only

# Analysis only (on already converted videos)
python3 simple_batch_processor_v2.py /path/to/videos --analyze-only
```

### `app.py` - Single Video Analysis

**Purpose**: Primary orchestrator for individual video analysis

**Command Line Interface**:
```bash
# Bypass interactive prompt
echo "n" | python3 app.py --input video.MP4 --output ./results

Options:
  --peek              Fast keyframe detection (5x faster, no tracking)
  --chapters          Aggregate chapter information into single video
  --live              Show live tracking video for debugging
  --conf              Confidence threshold (default: 0.25)
  --imgsz             Image processing size (default: 640)
  --species_classifier Path to optional species classifier
```

**Processing Flow**:
1. PyTorch compatibility patching for model loading
2. Video validation and preprocessing
3. Frame extraction with configurable stride
4. YOLO inference with tracking
5. Post-processing and result saving

---

## Video Processing Utilities

### `utils/video_iterators.py` - Video Frame Extraction

**Purpose**: Provides two distinct strategies for extracting frames from videos

**Functions**:

#### `stride_iterator(video_path, vid_stride)`
- **Purpose**: Precise frame extraction using OpenCV with configurable stride
- **Use Case**: Analyst mode for accurate tracking
- **Parameters**:
  - `video_path`: Path to video file
  - `vid_stride`: Frame skip interval (calculated from desired FPS)
- **Returns**: Generator yielding `(frame, timestamp_ms, frame_index)`

#### `keyframe_iterator(video_path)`
- **Purpose**: Fast keyframe extraction using PyAV
- **Use Case**: Peek mode for rapid detection without tracking
- **Returns**: Generator yielding `(frame_image, timestamp_ms, frame_index)`
- **Note**: Uses `skip_frame = 'NONKEY'` for performance optimization

**Implementation Details**:
- Automatic FPS calculation for stride determination
- Memory-efficient generator patterns
- Error handling for corrupted video files

---

### `utils/reformat_gopro.py` - GoPro Video Processing

**Purpose**: Handles GoPro-specific video format issues for compatibility

**Functions**:

#### `valid_video(video_path)`
- **Purpose**: Validates video file format and naming
- **Returns**: Boolean indicating if file is processable
- **Criteria**: `.mp4` or `.avi` extension, no hidden file prefix

#### `main(videos_root, output_root, stereo_prefix)`
- **Purpose**: Batch reformats GoPro videos to remove audio codec issues
- **Process**: Uses FFmpeg to extract video stream without audio
- **Command**: `ffmpeg -i input.mp4 -y -map 0:v -c copy output.mp4`

**Chapter Video Support**:
- Maintains directory structure during reformatting
- Supports stereo camera filtering by filename prefix
- Skips already processed videos for efficiency

---

## Annotation and Tracking Utilities

### `utils/sharktrack_annotations.py` - Core Annotation Processing

**Purpose**: Handles detection extraction, tracking post-processing, and output generation

**Key Functions**:

#### `extract_sightings(video_path, input_path, frame_results, frame_id, time, **kwargs)`
- **Purpose**: Converts YOLO detection results to standardised format
- **Returns**: List of detection dictionaries with bounding box coordinates
- **Features**:
  - Automatic directory structure parsing (`folder1`, `folder2`, etc.)
  - Track metadata generation for unique identification
  - Relative path computation for portability

#### `save_analyst_output(video_path, model_results, out_folder, next_track_index, **kwargs)`
- **Purpose**: Saves tracking results with post-processing and image generation
- **Process**:
  1. Apply post-processing filters
  2. Generate max-confidence detection images
  3. Save CSV outputs with track information
  4. Update global track index counter

#### `save_peek_output(video_path, frame_results, out_folder, next_track_index, **kwargs)`
- **Purpose**: Saves keyframe detection results for peek mode
- **Output**: Annotated frames with bounding box overlays

**Post-processing Logic**:
- **Length Threshold**: Tracks must persist ≥1 second
- **Motion Threshold**: Minimum 8% movement relative to frame size
- **Confidence Threshold**: 70% confidence for short/static tracks
- **False Positive Detection**: Combines multiple criteria

**Output Structure**:
```
output/
├── output.csv              # All detections with tracking
├── overview.csv            # Per-video summary
└── videos/
    └── {video_name}/
        └── {track_id}.jpg  # Max-confidence per track
```

---

### `utils/compute_maxn.py` - MaxN Metric Computation

**Purpose**: Post-processes cleaned annotations to compute MaxN (maximum number of individuals)

**Key Functions**:

#### `get_labeled_detections(internal_results_path, output_csv_path)`
- **Purpose**: Parses manually cleaned detection images
- **Expected Format**: `{track_id}-{species}.jpg` for classified detections
- **Returns**: Dictionary mapping track IDs to species labels

#### `clean_annotations_locally(sharktrack_df, labeled_detections)`
- **Purpose**: Filters raw detections to include only manually validated tracks
- **Process**: Updates species labels based on manual classification

#### `compute_species_maxn(cleaned_annotations, chapter)`
- **Purpose**: Calculates maximum simultaneous count per species
- **Grouping**: By video/chapter, species, and frame
- **Returns**: MaxN values with timestamps and track lists

#### `save_maxn_frames(cleaned_output, maxn, videos_path, analysis_output_path, chapters)`
- **Purpose**: Generates visualisation frames showing MaxN moments
- **Output**: Annotated images showing peak abundance per species

**Manual Review Workflow**:
1. Run SharkTrack in analyst mode
2. Review detection images in `internal_results/videos/`
3. Delete false positives
4. Rename valid detections: `{track_id}-{species}.jpg`
5. Run `compute_maxn.py` for final metrics

---

## Path and File Management

### `utils/path_resolver.py` - Path Handling Utilities

**Purpose**: Centralised path computation and file management

**Functions**:

#### `generate_output_path(user_output_path, input_path, annotation_folder, resume)`
- **Purpose**: Generates output directory with versioning
- **Versioning**: Automatic `v1`, `v2`, etc. for existing directories
- **Resume Support**: Reuses existing directory for continued processing

#### `remove_input_prefix_from_video_path(video_path, input)`
- **Purpose**: Converts absolute paths to relative for portability
- **Use Case**: Ensures output CSVs work across different systems

#### `compute_frames_output_path(video_path, input, output_path, chapters)`
- **Purpose**: Determines where to save detection images
- **Chapter Support**: Groups chapter videos under parent directory

#### `sort_files(files)`
- **Purpose**: Natural sorting of video files by numeric order
- **Implementation**: Regex extraction of numbers for proper sequencing

---

## Species Classification

### `utils/species_classifier.py` - DenseNet Species Classification

**Purpose**: Optional fine-grained species identification using deep learning

**Key Components**:

#### `SpeciesClassifier` Class
- **Architecture**: DenseNet121 backbone with custom classifier head
- **Input Processing**: Crop detection bounding boxes, resize to 200×400
- **Normalisation**: ImageNet statistics for transfer learning
- **Confidence Threshold**: 45% minimum for automatic classification

#### `build_species_classifier(classifier_path)` (Class Method)
- **Purpose**: Factory method for optional classifier instantiation
- **Requirements**: `classifier.pt` model file and `class_mapping.txt`

#### `__call__(row, image)` Method
- **Purpose**: Classifies individual detection patch
- **Input**: Pandas row with bounding box + full frame image
- **Output**: `(confidence, species_name)` tuple
- **Fallback**: Returns `None` for low-confidence predictions

**Integration**:
- Plugs into main pipeline via `--species_classifier` flag
- Automatic device detection (CUDA/CPU)
- Graceful degradation when model unavailable

---

## Time and Format Processing

### `utils/time_processor.py` - Time Format Conversions

**Purpose**: Bidirectional conversion between milliseconds and time strings

**Functions**:
- `ms_to_string(milliseconds)`: Converts to `HH:MM:SS.mmm` format
- `string_to_ms(time_string)`: Parses time strings back to milliseconds

**Use Cases**:
- CSV output formatting for human readability
- Video seeking operations
- Timestamp consistency across processing modes

---

## Image Processing and Visualisation

### `utils/image_processor.py` - Frame Processing Utilities

**Purpose**: Image extraction, annotation, and visualisation generation

**Key Functions**:
- `extract_frame_at_time(video_path, time_ms)`: Precise frame extraction
- `draw_bboxes(image, detections)`: Bounding box overlay rendering
- `annotate_image(image, metadata)`: Timestamp and metadata overlay

**Visualisation Features**:
- Confidence score display
- Track ID labelling
- Species classification overlay
- MaxN moment highlighting

---

## Configuration Management

### `utils/config.py` - System Configuration

**Purpose**: Centralised configuration constants and defaults

**Key Settings**:
- File naming conventions
- Processing thresholds
- Output format specifications
- Default parameter values

---

## Performance and Processing Optimisation

### Recent Additions (Enhanced Processing)

#### `utils/progress_converter.py` - Intelligent FFmpeg Conversion
- **Purpose**: GPU-accelerated video conversion with real-time monitoring
- **Features**: Size-weighted progress calculation, stall detection, adaptive timeouts
- **Integration**: Advanced batch processing with worker optimisation

#### `utils/gpu_accelerated_converter.py` - Hardware Acceleration
- **Purpose**: Leverages GPU resources for faster video processing
- **Compatibility**: Automatic fallback to CPU when GPU unavailable

#### `utils/worker_optimizer.py` - Parallel Processing
- **Purpose**: Optimises worker allocation based on system resources
- **Features**: CPU core detection, memory usage monitoring, load balancing

#### `utils/resumable_processor.py` - Fault Tolerance
- **Purpose**: Enables interrupted processing resumption
- **Implementation**: State tracking, checkpoint creation, intelligent restart

---

## Database and Integration Utilities

### `utils/database_integration.py` - Data Persistence
- **Purpose**: Database connectivity and data synchronisation
- **Features**: PostgreSQL integration, batch inserts, relationship management

### `utils/metadata_extractor.py` - Video Metadata
- **Purpose**: Extracts comprehensive video file information
- **Output**: Duration, resolution, codec, creation date, GPS coordinates

### `utils/substrate_classifier.py` - Habitat Classification
- **Purpose**: Automated seafloor habitat classification from video frames
- **Methods**: Computer vision techniques for substrate identification

---

## Model Architecture and Analysis

### `models/sharktrack.pt` - YOLOv8 Elasmobranch Detection Model

**Purpose**: Core deep learning model for detecting sharks and rays in underwater video footage

#### Model Structure & Space Breakdown

**File Size Analysis**:
- **Compressed**: 6.0 MB (sharktrack.pt)
- **Uncompressed**: 11.8 MB total parameter data
- **Compression ratio**: ~50% efficiency (typical PyTorch zip compression)

**Architecture Components**:
- **365 parameter files** organised as tensor chunks
- **Feature extraction layers**: ~2.9 MB (convolutional backbone)
- **Detection head weights**: ~2.4 MB (classification + localisation)
- **Metadata**: 120 KB (model architecture and training info)

**Largest Parameter Tensors**:
1. Final detection layer: 589 KB
2. Feature extraction blocks: 294 KB each (multiple)
3. Intermediate convolutions: 64-196 KB each

#### Role in Processing Pipeline

**Integration** (`app.py:33-85`):
```python
self.model_path = "models/sharktrack.pt"
model = YOLO(self.model_path)  # Ultralytics YOLOv8 wrapper
```

**Two Inference Modes**:
- **Analyst Mode**: Full tracking with BoT-SORT (`track_video()`)
- **Peek Mode**: Fast keyframe detection (`keyframe_detection()`)

**Processing Flow**:
1. Video frame extraction (3fps for tracking, keyframes for peek)
2. **YOLO inference** on each frame (elasmobranch detection)
3. Track assignment using BoT-SORT tracker
4. Post-processing & confidence filtering
5. MaxN computation from cleaned tracks

#### Training Data & Performance Relationship

**Current Model Specifications**:
- **Single-class detection**: "elasmobranch" (sharks + rays combined)
- **Detection accuracy**: 89% on BRUV footage
- **Processing speed**: 21x faster than manual annotation
- **Hardware requirements**: Standard laptop (CPU/GPU agnostic)

**Training Data Dependencies**:
- **Quality**: Diverse underwater conditions, lighting, water clarity
- **Quantity**: Balanced representation of species, sizes, orientations
- **Annotation**: Manually labeled bounding boxes on video frames
- **Specificity**: BRUV-optimised for baited station behaviour

**Model Skill Factors**:
- **Generalisation**: More diverse training data → better cross-region performance
- **Rare Species**: Larger datasets → improved detection of uncommon elasmobranchs
- **Regional Adaptation**: Location-specific training → enhanced local species accuracy

#### Global Resource Scaling Projections

**Current Foundation**: 6MB compressed, 12MB uncompressed per model

**Scaling Scenarios**:

**Phase 1: Regional Specialisation (5-10 models)**
- Regional ocean models: 5 × 6MB = **30MB total**
- Coverage: Atlantic, Pacific, Mediterranean, Arctic, Tropical regions

**Phase 2: Species-Specific Detection (20-50 models)**
- Fine-grained classification: 50 × 6MB = **300MB total**
- Target species: Great White, Tiger Shark, Hammerhead, Manta Ray, etc.

**Phase 3: Multi-Scale Ensemble (100+ models)**
- Combined regional + species + behavioural models
- Full ensemble: 100 × 6MB = **600MB total**
- Real-time model selection based on GPS location and metadata

**Phase 4: Continuous Learning Infrastructure**
- **Base model library**: 600MB (100 specialised models)
- **Monthly delta updates**: 1-5MB per region
- **Annual growth**: ~500MB/year with global research network expansion

**Infrastructure Requirements**:
- **Version Control**: Git LFS for efficient model versioning
- **Distribution**: CDN caching for regional model deployment
- **Blockchain Attribution**: Model contribution tracking via smart contracts
- **Incremental Updates**: Delta compression for model parameter updates

**Collaborative Training Ecosystem**:
- Federated learning across research institutions
- Contribution-weighted model ensemble voting
- Token rewards proportional to annotation quality and model improvement
- Automated performance benchmarking and model selection

The current 6MB model represents a highly optimised foundation that scales linearly with specialisation complexity, enabling a distributed global research network while maintaining computational efficiency.

---

## Testing and Quality Assurance

### Test Coverage
- Unit tests for core utilities (`tests/test_compute_maxn.py`)
- Integration tests for end-to-end workflows
- Performance benchmarks for optimization validation

### Error Handling
- Graceful degradation for missing dependencies
- Comprehensive error logging and reporting
- Automatic recovery mechanisms for processing failures

---

## Development Patterns and Conventions

### Architecture Principles
1. **Separation of Concerns**: Clear utility boundaries
2. **Generator Patterns**: Memory-efficient video processing
3. **Optional Dependencies**: Graceful feature degradation
4. **Path Agnostic**: Relative path usage for portability

### Code Conventions
- Pandas DataFrame standardisation
- Consistent error handling patterns
- Comprehensive type hints and documentation
- Device-agnostic processing (CPU/GPU)

### Integration Points
- Plugin architecture for species classifiers
- Configurable processing parameters
- Modular pipeline components
- Resume capability across sessions

---

This utility ecosystem enables SharkTrack to process marine video data efficiently while maintaining flexibility for diverse research workflows and hardware configurations. Each component is designed for modularity, allowing researchers to customise processing pipelines according to their specific requirements.