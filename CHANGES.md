# SharkTrack Fork: Changes for Upstream

This fork extends SharkTrack with deployment/retrieval detection, GoPro metadata extraction, a web GUI, species classifier training infrastructure, and numerous bug fixes. The changes emerged from analysing 319 BRUV videos across 94 stations, which exposed several bugs and motivated features that the original CLI workflow did not need.

All changes are organised into five PR-ready branches described at the end of this document.

## Bug Fixes

**Branch**: `pr/bugfixes` (base: `upstream/master`)

### PyTorch 2.6 `weights_only` patch

PyTorch 2.6 changed `torch.load()` to default `weights_only=True`, breaking model loading. A monkey-patch in `app.py` wraps `torch.load` to force `weights_only=False` when needed. (Upstream adopted a similar fix independently.)

### `frame_skip == 0` division-by-zero guard

`_get_frame_skip()` in `app.py` could return 0 on videos with unusual framerates, causing a `ZeroDivisionError` downstream. Now floors to 1.

### GoPro path quoting in `reformat_gopro.py`

FFmpeg commands failed on filenames containing spaces. Paths are now properly quoted. The function also skips the output directory during recursive walks, preventing infinite recursion when the output folder sits inside the input folder.

### Video validation and reformatting (`video_iterators.py`)

GoPro videos with metadata streams (timecode, telemetry) cause OpenCV read failures after 10-20 frames. Four new functions handle this:

- `validate_video_readable()` tests sequential frame reads
- `reformat_video_for_opencv()` strips non-video streams via FFmpeg (`-map 0:v -c copy`)
- `ensure_video_readable()` orchestrates test-then-reformat
- `cleanup_converted_video()` removes temporary copies after processing

`app.py` calls `ensure_video_readable()` before tracking and `cleanup_converted_video()` after.

### Windows subprocess fixes

All `subprocess.Popen` calls now use `sys.executable` instead of hardcoded `"python"`, which fails on Windows when `py.exe` is the launcher.

### Startup messages

`app.py` prints a startup message before importing PyTorch (which takes 10-30 seconds), so users know the process is loading.

### `.gitignore` and `requirements.txt`

`.gitignore` updated for thumbnails, checkpoint CSVs, user-trained classifiers, and test directories. `requirements.txt` adds Flask and click.


## Deployment/Retrieval Detection

**Branch**: `pr/deployment-detection` (base: `pr/bugfixes`)

### Purpose

BRUV videos contain three phases: deployment (camera lowered, unstable), stable recording (useful data), and retrieval (camera hauled out). Detecting these boundaries automatically serves two purposes: skipping deployment/retrieval frames during detection (fewer false positives from hands, boats, and surface), and computing accurate stable durations for standardised MaxN windows.

### Approach

`utils/deployment_detector.py` uses two-phase frame-differencing:

1. **Deployment**: Sample frames every 15 seconds. Compute normalised frame differences (0-1 motion score), smooth with a window of 3. Find the longest contiguous run below the stability threshold (0.15). The start of that run marks the deployment end.

2. **Retrieval**: Scan the last 50% of the video for contiguous high-motion blocks. Merge runs separated by single-sample gaps. Validate magnitude (mean > 0.25 or max > 0.4) to distinguish genuine camera haul-out from low-level noise. The onset of the first validated block is the retrieval start.

Key parameters: `sample_rate=15s`, `stability_threshold=0.15`, `min_stable_duration=60s`.

### Integration

`app.py --auto-skip-deployment` enables the detector. Frames outside the stable period are skipped during detection.

### Validation

Tested against 17 ground-truth videos with known deployment/retrieval times: 9 correct, 1 minor false positive (40 seconds), 0 missed detections, 7 conservative (detected stable period shorter than actual).

### Manual review workflow

`validate_deployment.py` generates an XLSX spreadsheet with per-video deployment results, motion plots, and columns for manual override values. Useful for verifying automated results before committing to them.


## GoPro Metadata Extraction

**Branch**: `pr/gopro-metadata` (base: `pr/bugfixes`)

`utils/metadata_extractor.py` extracts per-video metadata using three tools:

**Header data** (FFprobe + ExifTool): duration, FPS, resolution, codec, file size, creation time, camera model, serial number, firmware version, lens serial, field of view, auto-rotation.

**Frame analysis** (OpenCV): water clarity (edge density in central region), light level (mean brightness), substrate type (CV-based heuristic), substrate confidence.

Integration: `app.py --extract_metadata` saves per-video JSON files alongside detection results, then collates into `gopro_metadata.csv`.


## Web GUI

**Branch**: `pr/web-gui` (base: `pr/bugfixes`)

`web_gui.py` is a Flask-based control panel that replaces the CLI workflow:

- **Project Setup**: configure input/output paths, species classifier, metadata file
- **Detection**: run SharkTrack with real-time progress
- **Validation**: view and validate detections in the browser
- **Training**: extract frames, train species classifiers
- **Export**: combined metadata, MaxN results

Supporting files:

- `start_sharktrack.py`: cross-platform launcher (handles venv activation, dependency checks)
- `utils/config_loader.py`: configuration management
- `templates/control_panel.html`: main GUI (2,933 lines)
- `templates/index.html`: detection results viewer (1,281 lines)
- `START_SHARKTRACK.bat`, `START_SHARKTRACK.command`, `launch_gui.sh`: platform-specific launchers
- `setup_gui.sh`: first-run setup script


## Species Classifier Enhancements

**Branch**: `pr/classifier-training` (base: `pr/bugfixes`)

Four new modules add training and inference infrastructure:

- `utils/train_species_classifier.py` (504 lines): full DenseNet121 training pipeline with data augmentation, learning rate scheduling, mixed precision, and checkpoint continuation. Accepts `--metadata_csv` and `--validation_csv` to embed provenance (GPS, region, substrate, validators) in the trained model's metadata.

- `utils/training_frame_extractor.py` (420 lines): extracts training frames from videos at detection timestamps, crops to bounding box coordinates.

- `utils/checkpoint_manager.py` (648 lines): distributed training checkpoints with provenance tracking. Each checkpoint saves model weights, optimizer state, replay samples (for anti-forgetting), and a manifest recording GPS locations, region, country, habitat, substrate types, water clarity, depth range, camera models, collection dates, and validator IDs. Provenance is extracted from metadata CSVs (produced by `MetadataExtractor`) and validation CSVs (exported from the validation HTML). Supports lineage tracking across multiple training generations.

- `utils/parallel_classifier.py` (257 lines): batched species classification with LRU frame caching. Processes multiple detections per video read instead of one at a time.


## Post-Processing Filters

**`utils/surface_filter.py`** (308 lines): probabilistic filter using four weighted features (vertical position 0.30, expected surface location by depth 0.25, blue channel variance 0.25, texture patterns 0.20) to downweight detections likely to be surface objects (waves, sargassum, equipment). Integrated via `app.py --filter_surface`.

Substrate classification is handled by `metadata_extractor.py` using CV-based heuristics (HSV colour, texture variance, edge density) on sampled frames.


## Validation and Analysis Tools

**`generate_validation_thumbnails.py`** (1,704 lines): extracts one thumbnail per track (highest-confidence frame), then generates a self-contained interactive HTML page for validation. Supports filters, batch tagging, CSV export, and localStorage persistence.

**`update_predictions.py`** (448 lines): temporal smoothing and label propagation. Applies validated species labels to unvalidated tracks in the same video based on temporal proximity and track similarity.

**`reclassify_unvalidated.py`** (242 lines): re-runs the species classifier on unvalidated tracks by cropping from existing thumbnails using bounding box coordinates. Checkpoints progress every 50 tracks.

**`build_station_level_maxn.py`** (227 lines): aggregates chapter-level MaxN to station level using a configurable time window (default 60 minutes from stable start). Handles multi-chapter GoPro recordings and manual deployment overrides.

**`plot_duration_maxn.R`**: diagnostic R script producing a stacked-bar plot of stable duration versus MaxN per station, with track tick marks and a 60-minute reference line.


## New Files Summary

### Core pipeline additions

| File | Lines | Purpose |
|------|------:|---------|
| `utils/deployment_detector.py` | 423 | Deployment/retrieval detection via frame-differencing |
| `utils/metadata_extractor.py` | 668 | GoPro metadata extraction (FFprobe + ExifTool + OpenCV) |
| `utils/metadata_merger.py` | 343 | Merge metadata from multiple sources |
| `validate_deployment.py` | 360 | XLSX export for manual deployment review |

### Web GUI

| File | Lines | Purpose |
|------|------:|---------|
| `web_gui.py` | 1,313 | Flask web interface |
| `start_sharktrack.py` | 359 | Cross-platform launcher |
| `utils/config_loader.py` | 385 | Configuration management |
| `templates/control_panel.html` | 2,933 | Main control panel |
| `templates/index.html` | 1,281 | Detection results viewer |
| `START_SHARKTRACK.bat` | 89 | Windows launcher |
| `START_SHARKTRACK.command` | 130 | macOS/Linux launcher |
| `launch_gui.sh` | 97 | Linux launcher |
| `setup_gui.sh` | 55 | Setup script |

### Species classifier infrastructure

| File | Lines | Purpose |
|------|------:|---------|
| `utils/train_species_classifier.py` | 504 | Training pipeline (DenseNet121, augmentation, provenance) |
| `utils/training_frame_extractor.py` | 420 | Frame extraction at detection timestamps |
| `utils/checkpoint_manager.py` | 648 | Distributed training checkpoints with provenance |
| `utils/parallel_classifier.py` | 257 | Batched classification with frame caching |

### Post-processing and validation

| File | Lines | Purpose |
|------|------:|---------|
| `utils/surface_filter.py` | 308 | Surface false-positive filter |
| `generate_validation_thumbnails.py` | 1,704 | Thumbnail extraction and validation HTML |
| `update_predictions.py` | 448 | Temporal smoothing and label propagation |
| `reclassify_unvalidated.py` | 242 | Re-classify unvalidated tracks from thumbnails |
| `build_station_level_maxn.py` | 227 | Station-level MaxN aggregation |

### Modified upstream files

| File | Lines | Nature of change |
|------|------:|------------------|
| `app.py` | 391 | Bug fixes, deployment detection, metadata extraction, video validation |
| `utils/video_iterators.py` | 204 | Four new functions for video validation/reformatting |
| `utils/reformat_gopro.py` | 54 | Path quoting, output directory skip |
| `utils/sharktrack_annotations.py` | 505 | Raw detection export, metadata integration |
| `utils/image_processor.py` | 113 | `extract_frame_at_time()` for training |
| `utils/species_classifier.py` | 74 | CPU fallback, DenseNet loading |
| `utils/compute_maxn.py` | 138 | Edge case fixes |
| `utils/path_resolver.py` | 59 | Path handling fixes |


## PR Strategy

Five branches, each self-contained and reviewable independently.

| Branch | Base | Scope |
|--------|------|-------|
| `pr/bugfixes` | `upstream/master` | All bug fixes: PyTorch patch, frame_skip guard, GoPro path quoting, video validation, Windows subprocess, startup messages, .gitignore, requirements.txt |
| `pr/deployment-detection` | `pr/bugfixes` | `utils/deployment_detector.py`, `validate_deployment.py`, `--auto-skip-deployment` integration in `app.py` |
| `pr/gopro-metadata` | `pr/bugfixes` | `utils/metadata_extractor.py`, `utils/metadata_merger.py`, `--extract_metadata` integration in `app.py` |
| `pr/web-gui` | `pr/bugfixes` | `web_gui.py`, `start_sharktrack.py`, `utils/config_loader.py`, `templates/`, launchers, `setup_gui.sh` |
| `pr/classifier-training` | `pr/bugfixes` | `utils/train_species_classifier.py`, `utils/training_frame_extractor.py`, `utils/checkpoint_manager.py`, `utils/parallel_classifier.py` (includes provenance tracking) |

The bugfixes branch is the foundation. The other four branch from it independently and can be merged in any order. Filippo has already adopted the PyTorch monkey-patch via issue #6, so some coordination on the bugfixes branch may be needed.
