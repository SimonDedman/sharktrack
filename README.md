# SharkTrack 1.5

AI-powered shark and ray detection for BRUV video analysis, with human validation workflow and MaxN calculation.

## Quick Start

### 1. Install Python (if not already installed)

Download and install Python 3.10+ from https://www.python.org/downloads/

**Windows users:** Check "Add Python to PATH" during installation!

### 2. Download the Model File

Download `sharktrack.pt` (6MB) and place it in the `models/` folder:
- [Download from original repo](https://github.com/filippovarini/sharktrack/raw/master/models/sharktrack.pt)

### 3. Launch SharkTrack

**Windows:** Double-click `START_SHARKTRACK.bat`

**Mac:** Double-click `START_SHARKTRACK.command`

**Linux:** Run `./launch_gui.sh`

Your browser will open automatically to the Control Panel.

First launch will take a few minutes to install dependencies.

## What SharkTrack Does

1. **Detection** - Runs AI detection on your BRUV videos to find sharks, rays, and other marine life
2. **Thumbnail Generation** - Creates visual thumbnails for human review
3. **Human Validation** - Interactive interface to verify detections and identify species
4. **Smart Suggestions** - AI learns from your validations and suggests species for remaining tracks
5. **MaxN Calculation** - Computes standard BRUV metrics from validated data

## System Requirements

- **Python 3.8+** (3.10 recommended)
- **GPU** (optional but recommended) - NVIDIA CUDA or Apple Silicon
- **RAM**: 8GB minimum, 16GB recommended
- **Disk**: Space for output files (~10% of video size)

## First-Time Setup

The Control Panel will guide you through:

1. **Your Name/Initials** - For identifying your validation exports
2. **Input Videos Folder** - Where your BRUV videos are stored
3. **Output Results Folder** - Where SharkTrack saves results
4. **Video Collections** - Map collection names to their folder paths (for opening videos from thumbnails)

Configuration is stored in your browser and synced to `sharktrack_config.json`.

## Workflow Overview

```
Videos → Detection → Thumbnails → Human Validation → MaxN
                           ↑                ↓
                           └── Smart Suggestions ←┘
```

### The Validation Cycle

Validation is **iterative**:

1. Review some thumbnails and mark TRUE/FALSE detections
2. Identify species for TRUE detections
3. Export your results (CSV with your initials)
4. Run "Smart Suggestions" - AI learns from your labels
5. Regenerate the validation HTML with predictions
6. Review again - now with AI assistance!

Each cycle gets faster as the AI learns your project's species.

### Batch Tagging

For efficiency, select multiple similar tracks and apply labels at once:
- Filter to high-confidence detections
- Select all clearly correct detections
- Apply species label to all at once
- Repeat for false positives (debris, reflections, etc.)

## Multi-User Validation

Multiple people can validate simultaneously:

1. Each person sets up their own paths in the Control Panel (the same shared folder will have different paths on different machines)
2. Each person exports their CSV with their initials (`validation_results_TG.csv`, `validation_results_SIMON.csv`)
3. SharkTrack automatically merges all validation files when generating smart suggestions

## File Structure

After processing:

```
your_output_folder/
├── analysed/
│   └── [video_name]/
│       ├── output.csv          # Raw detections
│       └── thumbnails/         # Detection images
├── validation/
│   ├── thumbnails/             # Validation thumbnails
│   ├── validation.html         # Interactive validation interface
│   ├── validation_results.csv  # Your validated data
│   └── smart_predictions.json  # AI suggestions
└── maxn/
    └── maxn_results.csv        # Final MaxN calculations
```

## Troubleshooting

### "Python not found"
Install Python 3.10+ from https://www.python.org/downloads/
On Windows, check "Add Python to PATH" during installation.

### "No GPU detected"
SharkTrack works on CPU (just slower). For GPU:
- NVIDIA: Install CUDA toolkit
- Mac: Apple Silicon M1/M2/M3 automatically detected

### "Thumbnails not loading"
Check your Video Collections mapping in Project Setup - the paths must match your local filesystem.

## Attribution

SharkTrack is based on [MoveTrack](https://github.com/filippovarini/sharktrack) by Filippo Varini.

## License

GPL-3.0

---

For detailed documentation, see the `docs/` folder or visit the [GitHub repository](https://github.com/SimonDedman/sharktrack).
