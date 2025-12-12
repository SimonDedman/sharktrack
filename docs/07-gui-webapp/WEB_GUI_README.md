# SharkTrack Web GUI

## Overview

The SharkTrack Web GUI provides a comprehensive, browser-based interface for all SharkTrack functionality. Access all features through an intuitive web interface without needing to use the command line.

## Features

### 1. **Analysis Tab**
Run SharkTrack analysis with full control over all parameters:

**Basic Settings:**
- Input/Output paths with file browser
- Confidence threshold (0-1)
- Image size (512-1280px)
- Max videos to process
- Stereo prefix filtering

**Advanced Features:**
- ✅ **Auto-detect Deployment/Retrieval**: Automatically skip unstable periods
- ✅ **Peek Mode**: 5x faster processing (no MaxN tracking)
- ✅ **Chapter Videos**: Aggregate multi-chapter videos
- ✅ **Resume**: Continue interrupted analyses
- ✅ **Deployment Stability Threshold**: Tune sensitivity (0-1)

**Species Classification:**
- Specify path to trained classifier
- Link to Classifier Training tab

**Real-time Monitoring:**
- Live output console
- Progress tracking
- Stop/start controls

### 2. **Deployment Detection Tab**
Analyze individual videos for deployment/retrieval periods:

- Point to any video file
- Get recommended skip_start and skip_end times
- View full analysis output
- Use results in Analysis tab

**Use Case**: Test deployment detection on individual videos before running batch analysis.

### 3. **Classifier Training Tab**
Train custom species classifiers from labeled images:

**Requirements:**
- Directory of labeled images (either subdirectories by class OR filenames containing class names)
- Class names (comma-separated)
- Output path for trained model

**Configuration:**
- Training epochs (default 25)
- Batch size (default 16)
- Automatic train/validation split (80/20)

**Output:**
- `classifier.pt` - Trained model weights
- `class_mapping.txt` - Species list
- `training_history.json` - Training metrics
- `metadata.json` - Training configuration

**Example:**
```
Training Images: /path/to/thumbnails/
Class Mapping: G.cirratum,C.perezi,C.acronotus,non_elasmobranch
Output Model: models/caribbean_sharks_v1
```

### 4. **Results Tab**
View and analyze completed analyses:

**Displays:**
- Total detections
- Unique tracks (MaxN)
- Videos processed
- Species distribution chart
- Sample detection data

**Use Case**: Quick validation of analysis results without opening CSV files.

### 5. **System Tab**
Monitor system resources and active processes:

**System Info:**
- CPU cores
- Total/Available memory
- GPU availability
- CUDA version

**Active Processes:**
- View all running analyses
- Check status (running/completed/failed)
- Monitor elapsed time
- See output paths

## Installation

### Prerequisites
```bash
cd /home/simon/Installers/sharktrack-1.5
source sharktrack-env/bin/activate
pip install flask
```

## Running the GUI

### Start the Web Server
```bash
python3 web_gui.py
```

### Access the Interface
Open your browser to:
```
http://localhost:5000
```

**Or from another device on the network:**
```
http://<your-ip-address>:5000
```

## Usage Examples

### Example 1: Basic Analysis with Deployment Detection

1. **Go to Analysis Tab**
2. **Set Input Path**: `/media/simon/Extreme SSD/BRUV_Summer_2022_46_62`
3. **Enable "Auto-detect Deployment/Retrieval"**
4. **Set Confidence**: `0.25`
5. **Click "Start Analysis"**
6. **Monitor Progress** in real-time console

### Example 2: Train Classifier from Validation Data

1. **Go to Classifier Training Tab**
2. **Training Images**: `/path/to/validation/thumbnails`
3. **Class Mapping**: `G.cirratum,C.perezi,C.acronotus,non_elasmobranch`
4. **Output Model**: `models/caribbean_sharks_v1`
5. **Epochs**: `25`
6. **Click "Start Training"**
7. **Wait 30-60 minutes** for training to complete

### Example 3: Analyze Deployment Period

1. **Go to Deployment Detection Tab**
2. **Video Path**: `/media/simon/.../BRUV 52/GH012492.MP4`
3. **Click "Analyze Deployment"**
4. **View Results**:
   - Skip Start: 128.0s
   - Skip End: 0.2s
5. **Use values in Analysis Tab** (or let auto-detection handle it)

## Advanced Features

### Surface Probability Filter

The surface filter is automatically integrated into the analysis pipeline when using the Web GUI. It:

1. **Estimates surface probability** for each detection based on:
   - Vertical position in frame
   - Expected surface location (from depth metadata)
   - Blue channel variance (waves have high variance)
   - Texture patterns (edges, gradients)

2. **Downweights confidence** for likely surface objects (probability > 0.7):
   - Original confidence × (1 - surface_prob × 0.5)
   - Example: 0.90 confidence with 0.80 surface prob → 0.54 final confidence

3. **Tracks filtering** in output CSV:
   - `surface_probability` column added
   - `surface_filtered` boolean flag
   - `original_confidence` preserved

**Expected Impact**: Reduces false positives from sargassum, surface waves, and floating debris.

### Deployment Detection Integration

When "Auto-detect Deployment/Retrieval" is enabled:

1. **Per-video analysis**: Each video analyzed independently (deployment times vary)
2. **Automatic skipping**: Frames outside stable period not processed
3. **Performance**: ~30-60s analysis overhead, compensated by fewer frames
4. **Output logging**: Shows detected stable period and frames skipped

**Tuning Stability Threshold**:
- **Default (0.15)**: Balanced detection
- **Increase (0.20-0.25)**: More lenient, less aggressive filtering
- **Decrease (0.10-0.12)**: More strict, catches subtle instability

## API Endpoints

The web GUI exposes RESTful API endpoints for programmatic access:

### Analysis
- `POST /api/analyze/start` - Start new analysis
- `GET /api/analyze/status/<process_id>` - Check status
- `POST /api/analyze/stop/<process_id>` - Stop running analysis
- `GET /api/analyze/list` - List all processes

### Deployment Detection
- `POST /api/deployment/analyze` - Analyze video for deployment periods

### Classifier Training
- `POST /api/classifier/train` - Start classifier training

### Results
- `GET /api/results/<path>` - Get analysis results

### System
- `GET /api/system/info` - Get system information
- `GET /api/files/browse?path=<path>` - Browse filesystem

## Troubleshooting

### Port Already in Use
```bash
# Change port in web_gui.py (line 647):
app.run(host='0.0.0.0', port=5001, debug=True)
```

### Permission Denied on Folders
The web server runs with your user permissions. Ensure you have read/write access to:
- Input video directories
- Output directories
- Model directories

### Can't Access from Other Devices
```bash
# Check firewall allows port 5000
sudo ufw allow 5000

# Find your IP address
ip addr show

# Access from other device:
http://<your-ip>:5000
```

### Analysis Not Starting
1. Check System Tab for available resources
2. Verify input path exists and contains valid videos
3. Check output console for error messages
4. Ensure virtual environment is activated

## Performance Tips

### CPU-Only Systems
- Use `imgsz=512` for faster processing
- Enable Peek Mode for 5x speedup (no tracking)
- Reduce batch size if memory is limited

### GPU Systems
- Use `imgsz=640` or `imgsz=800` for better accuracy
- GPU automatically detected and used
- Monitor GPU memory in System Tab

### Large Datasets
- Enable "Resume" to continue after interruptions
- Use deployment detection to skip ~20% of frames
- Process in batches with `limit` parameter

## Next Steps

After completing your analysis:

1. **Review Results Tab** for summary statistics
2. **Check output.csv** for detailed detections
3. **Examine thumbnails** in output directory
4. **Train classifier** if species identification needed
5. **Generate validation template** for quality control

## Related Documentation

- `DEPLOYMENT_DETECTION_README.md` - Deployment detection details
- `docs/01-core-system/UTILITIES_DOCUMENTATION.md` - Lower-level scripts
- `generate_validation_template.py` - Create validation CSVs
- `utils/surface_filter.py` - Surface filter implementation
- `utils/train_species_classifier.py` - Classifier training details

## Support

For issues, questions, or feature requests:
- Check existing documentation in `/docs`
- Review validation results for false positive patterns
- Test deployment detection on individual videos first
- Monitor system resources during processing

## Future Enhancements

Planned features for future releases:
- Real-time video preview with detection overlays
- Batch operations (multiple input directories)
- Collaborative review interface (Galaxy Zoo for sharks)
- Integration with Global FinPrint database
- BitTorrent-based dataset distribution
- Results export to GitHub Pages
