# SharkTrack Complete Workflow

## Overview

This document describes the end-to-end workflow from raw BRUV videos to validated species detection results.

---

## Workflow Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ PHASE 1: DETECTION (Automated)                                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  [BRUV Videos]  ──►  [SharkTrack Detection]  ──►  [Raw Detection CSVs]     │
│   (External HDD)      app.py / web_gui.py         (Project folder)          │
│   ~500GB-2TB          Uses: sharktrack.pt         ~30-50MB per project      │
│                       [GLOBAL]                                              │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ PHASE 2: VALIDATION PREP (Semi-automated)                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  [Raw Detection CSVs]  ──►  [generate_validation_thumbnails.py]            │
│                                      │                                      │
│                                      ▼                                      │
│                         ┌────────────────────────┐                          │
│                         │  validation/           │                          │
│                         │  ├── thumbnails/       │  ~700MB (2950 images)   │
│                         │  ├── validation.html   │  ~2MB                   │
│                         │  └── thumbnail_meta... │  ~700KB                 │
│                         └────────────────────────┘                          │
│                                [PROJECT]                                    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ PHASE 3: HUMAN VALIDATION (Manual - Browser)                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  User opens validation.html in browser                                      │
│       │                                                                     │
│       ├──► Views thumbnails, marks TRUE/FALSE                               │
│       ├──► Assigns taxon_group (shark/ray/teleost/etc)                     │
│       ├──► Assigns species (Ginglymostoma cirratum, etc)                   │
│       ├──► Filters by confidence, collection, BRUV, validation status      │
│       ├──► Uses batch tagging for efficiency                               │
│       │                                                                     │
│       └──► Exports CSV when done/pausing                                   │
│                         │                                                   │
│                         ▼                                                   │
│              validation_results_TG.csv  (~600KB)                           │
│                      [PROJECT]                                              │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ PHASE 4: SMART SUGGESTIONS (Automated)                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  [validation_results_TG.csv]  ──►  [update_predictions.py]                 │
│                                           │                                 │
│                                           ▼                                 │
│                         ┌─────────────────────────────────┐                │
│                         │  smart_predictions.json (~700KB) │                │
│                         │  suggestion_history.json (~80KB) │                │
│                         └─────────────────────────────────┘                │
│                                      [PROJECT]                              │
│                                                                             │
│  Algorithm: Temporal proximity voting                                       │
│  - Finds validated tracks within 2-min window                              │
│  - Suggests species based on weighted voting                               │
│  - Tracks accuracy of previous suggestions                                 │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ PHASE 5: REGENERATE HTML (Automated)                                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  [generate_validation_thumbnails.py]                                        │
│       │                                                                     │
│       ├──► Embeds existing validations from CSV                            │
│       ├──► Embeds smart predictions from JSON                              │
│       └──► Generates fresh validation.html                                 │
│                                                                             │
│  Loop back to PHASE 3 until all tracks validated                           │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ PHASE 6: CLASSIFIER TRAINING (Optional - for future projects)              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  [validation_results_TG.csv]  ──►  [prepare_classifier_training_data.py]   │
│  [thumbnails/]                              │                               │
│                                             ▼                               │
│                         ┌─────────────────────────────────┐                │
│                         │  CLASSIFIER_TRAINING_DATA/      │                │
│                         │  ├── Ginglymostoma_cirratum/    │                │
│                         │  ├── Carcharhinus_perezi/       │                │
│                         │  ├── FALSE_human/               │                │
│                         │  └── ...                        │                │
│                         └─────────────────────────────────┘                │
│                                                                             │
│  [train_species_classifier.py]  ──►  classifier.pt + class_mapping.txt    │
│                                              [GLOBAL]                       │
│                                                                             │
│  Future projects can use trained classifier for auto species ID            │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ PHASE 7: MAXN & METRICS CALCULATION (Automated)                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  [validation_results.csv]  ──►  [calculate_maxn.py]                        │
│  [reanalysis_all_tracks.csv]          │                                    │
│                                       ▼                                     │
│                         ┌─────────────────────────────────┐                │
│                         │  maxn_results_by_video.csv      │                │
│                         │  maxn_results_by_station.csv    │                │
│                         └─────────────────────────────────┘                │
│                                                                             │
│  Outputs include:                                                          │
│  - MaxN per taxon group (shark, ray_skate, teleost)                        │
│  - MaxN per species                                                        │
│  - Species richness counts                                                 │
│  - Track counts and total time in frame                                    │
│  - Species lists per video/station                                         │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ PHASE 8+: FUTURE ENHANCEMENTS (Planned)                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  GUI Integration:                                                          │
│  - "Generate MaxN Report" button in validation.html                        │
│  - Unified GUI for all workflow phases                                     │
│  - Progress indicators between phases                                      │
│                                                                             │
│  Additional Analysis:                                                      │
│  - HTML dashboard with summary statistics                                  │
│  - Bar charts of MaxN by station                                          │
│  - Species accumulation curves                                             │
│  - Maps (if GPS coordinates available)                                    │
│  - First/last appearance times                                            │
│  - Average confidence per species                                         │
│                                                                             │
│  Data Quality:                                                             │
│  - Auto-detection of misclassifications (e.g., ray in shark group)        │
│  - Validation completeness reports                                         │
│  - Track viewer for debugging detection gaps                              │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Detailed Step Reference

### PHASE 1: Detection

| Step | Action | Script/Tool | GUI? | Input | Output | Size | Scope |
|------|--------|-------------|------|-------|--------|------|-------|
| 1.1 | Run SharkTrack detection | `app.py` or `web_gui.py` | Yes (web_gui) | BRUV videos (.MP4) | Detection CSVs | ~30-50MB | PROJECT |
| 1.2 | Model used | `models/sharktrack.pt` | - | - | - | 6MB | GLOBAL |

**Commands:**
```bash
# CLI mode
python app.py -i /path/to/videos -o /path/to/output

# Web GUI mode
python web_gui.py
# Then open http://localhost:5000
```

**Output files:**
- `{output}/reanalysis_all_tracks.csv` - All detection tracks with bounding boxes
- `{output}/reanalysis_all_raw_detections.csv` - Raw frame-by-frame detections
- `{output}/bruv_summary.csv` - Summary per BRUV station

---

### PHASE 2: Validation Preparation

| Step | Action | Script/Tool | GUI? | Input | Output | Size | Scope |
|------|--------|-------------|------|-------|--------|------|-------|
| 2.1 | Generate thumbnails + HTML | `generate_validation_thumbnails.py` | No | tracks CSV | thumbnails/ + validation.html | ~700MB | PROJECT |

**Commands:**
```bash
python generate_validation_thumbnails.py
```

**Output files:**
- `validation/thumbnails/` - One JPG per unique track (~235KB avg, 2950 images = 694MB)
- `validation/validation.html` - Interactive validation interface (~2MB)
- `validation/thumbnail_metadata.csv` - Track metadata (~700KB)

---

### PHASE 3: Human Validation

| Step | Action | Script/Tool | GUI? | Input | Output | Size | Scope |
|------|--------|-------------|------|-------|--------|------|-------|
| 3.1 | Validate in browser | `validation.html` | Yes (browser) | HTML + thumbnails | validation_results.csv | ~600KB | PROJECT |

**User actions:**
1. Open `validation.html` in browser
2. For each track: mark TRUE/FALSE, assign group, assign species
3. Use filters (confidence, collection, validation status)
4. Use batch tagging for similar tracks
5. Click "Export CSV" to save progress

**Output files:**
- `validation_results.csv` or `validation_results_TG.csv` - Validation labels

---

### PHASE 4: Smart Suggestions

| Step | Action | Script/Tool | GUI? | Input | Output | Size | Scope |
|------|--------|-------------|------|-------|--------|------|-------|
| 4.1 | Generate predictions | `update_predictions.py` | No | validation CSV | smart_predictions.json | ~700KB | PROJECT |
| 4.2 | Track accuracy | `update_predictions.py` | No | validation CSV | suggestion_history.json | ~80KB | PROJECT |

**Commands:**
```bash
python update_predictions.py
```

**Output files:**
- `validation/smart_predictions.json` - Species suggestions for unvalidated tracks
- `validation/suggestion_history.json` - Accuracy tracking (correct/incorrect/pending)

**Algorithm:**
- Temporal proximity: tracks within 2-minute window of validated tracks
- Weighted voting by confidence and time distance
- Tracks suggestion accuracy over validation rounds

---

### PHASE 5: Regenerate HTML

| Step | Action | Script/Tool | GUI? | Input | Output | Size | Scope |
|------|--------|-------------|------|-------|--------|------|-------|
| 5.1 | Regenerate with suggestions | `generate_validation_thumbnails.py` | No | CSV + JSON | validation.html | ~2MB | PROJECT |

**Commands:**
```bash
python generate_validation_thumbnails.py
```

**What gets embedded:**
- Existing validations from CSV (preloaded in browser)
- Smart predictions from JSON (shown with purple badges)

---

### PHASE 6: Classifier Training (Optional)

| Step | Action | Script/Tool | GUI? | Input | Output | Size | Scope |
|------|--------|-------------|------|-------|--------|------|-------|
| 6.1 | Prepare training data | `prepare_classifier_training_data.py` | No | validation CSV + thumbnails | class folders | varies | PROJECT |
| 6.2 | Train classifier | `utils/train_species_classifier.py` | No | class folders | classifier.pt | ~25MB | GLOBAL |

**Commands:**
```bash
# Prepare data
python prepare_classifier_training_data.py

# Train classifier
python utils/train_species_classifier.py \
  --training_images /path/to/training_data \
  --class_mapping "Ginglymostoma_cirratum,Carcharhinus_perezi,..." \
  --output_model models/
```

**Output files:**
- `models/classifier.pt` - Trained species classifier (GLOBAL - reusable)
- `models/class_mapping.txt` - Species index mapping (GLOBAL)

---

### PHASE 7: MaxN & Metrics Calculation

| Step | Action | Script/Tool | GUI? | Input | Output | Size | Scope |
|------|--------|-------------|------|-------|--------|------|-------|
| 7.1 | Calculate MaxN & metrics | `calculate_maxn.py` | No | validation CSV + tracks CSV | maxn_results*.csv | ~50KB | PROJECT |

**Commands:**
```bash
python calculate_maxn.py
```

**Output files:**
- `validation/maxn_results_by_video.csv` - Per-video metrics
- `validation/maxn_results_by_station.csv` - Per-BRUV station metrics (aggregated)

**Metrics calculated:**

| Metric | Video-level | Station-level | Description |
|--------|-------------|---------------|-------------|
| `maxn_shark` | max in any frame | max across videos | Maximum sharks visible simultaneously |
| `maxn_ray_skate` | max in any frame | max across videos | Maximum rays/skates visible simultaneously |
| `maxn_elasmobranch` | shark + ray | shark + ray | Combined elasmobranch MaxN |
| `maxn_teleost` | max in any frame | max across videos | Maximum teleosts visible simultaneously |
| `maxn_{species}` | max in any frame | max across videos | MaxN per shark species |
| `n_shark_tracks` | count | sum | Number of unique shark tracks |
| `shark_total_time_sec` | sum of durations | sum | Total seconds sharks visible |
| `shark_species_richness` | unique count | unique count | Number of shark species |
| `shark_species_list` | comma-separated | comma-separated | List of species present |

**Algorithm notes:**
- MaxN is calculated per-frame: count of distinct track_ids visible in each frame
- Station-level MaxN = maximum of video-level MaxN values (standard BRUV protocol)
- Station-level species richness = unique species across all videos (not sum)
- Time in frame = sum of (last_frame - first_frame) / fps for each track

---

## File Inventory

### GLOBAL Files (Reusable across projects)

| File | Description | Size | Location |
|------|-------------|------|----------|
| `sharktrack.pt` | YOLO detection model (sharks/rays) | 6MB | `models/` |
| `classifier.pt` | Species classifier (after training) | ~25MB | `models/` |
| `class_mapping.txt` | Species class indices | <1KB | `models/` |

### PROJECT Files (Per-project outputs)

| File | Description | Typical Size | Location |
|------|-------------|--------------|----------|
| `reanalysis_all_tracks.csv` | All detection tracks | 30-50MB | project root |
| `reanalysis_all_raw_detections.csv` | Frame-by-frame detections | 30-50MB | project root |
| `thumbnails/` | One image per track | 500MB-1GB | `validation/` |
| `validation.html` | Interactive validation UI | 2-3MB | `validation/` |
| `validation_results*.csv` | Human validation labels | 500KB-1MB | `validation/` |
| `smart_predictions.json` | Auto-suggestions | 500KB-1MB | `validation/` |
| `suggestion_history.json` | Accuracy tracking | 50-100KB | `validation/` |
| `maxn_results_by_video.csv` | MaxN & metrics per video | ~50KB | `validation/` |
| `maxn_results_by_station.csv` | MaxN & metrics per BRUV station | ~10KB | `validation/` |
| `calculate_maxn.py` | MaxN calculation script | ~10KB | `validation/` |

---

## Platform Compatibility

### Current State

| Component | Windows | macOS | Linux | Notes |
|-----------|---------|-------|-------|-------|
| `app.py` (CLI) | ✅ | ✅ | ✅ | Requires Python 3.10+ |
| `web_gui.py` | ✅ | ✅ | ✅ | Flask-based |
| `validation.html` | ✅ | ✅ | ✅ | Any modern browser |
| `generate_validation_thumbnails.py` | ⚠️ | ⚠️ | ✅ | Hardcoded paths |
| `update_predictions.py` | ⚠️ | ⚠️ | ✅ | Hardcoded paths |

### Required for Production

1. **Path configuration**: Replace hardcoded paths with config file or CLI args
2. **Bundled distribution**: Package as standalone app (PyInstaller/electron)
3. **Video path handling**: Handle different drive mount points across OS
4. **Browser compatibility**: Test localStorage persistence across browsers

---

## Distributed Validation Workflow

For sending validation to remote collaborators (e.g., Tristan):

```
YOU (scripts)                         COLLABORATOR (browser only)
─────────────────                     ──────────────────────────

1. Run update_predictions.py
2. Run generate_validation_thumbnails.py

3. Create zip:
   zip -r validation_YYYYMMDD.zip \
     validation/validation.html \
     validation/thumbnails/
   (Exclude: *.json, *_TG.csv)

4. Send zip (~700MB) ──────────────►  5. Unzip
                                      6. Open validation.html
                                      7. Validate tracks
                                      8. Export CSV

9. Receive CSV ◄─────────────────────  Sends validation_results.csv

10. Copy to validation/ folder
11. Rename to validation_results_TG.csv
12. Run update_predictions.py
    - Shows accuracy report
    - Updates suggestion_history.json
13. Loop from step 2...
```

---

## Accuracy Tracking Output

After running `update_predictions.py`:

```
======================================================================
SUGGESTION ACCURACY REPORT
======================================================================

Total suggestions made: 304
  Correct:   245
  Incorrect: 23
  Pending:   36

Accuracy (of resolved): 91.4%

Confusion Matrix (where suggestions were wrong):
  Suggested -> Actually was:
    Carcharhinus perezi -> Carcharhinus acronotus: 8
    Ginglymostoma cirratum -> FALSE_POSITIVE: 5
    Carcharhinus acronotus -> Carcharhinus perezi: 4
    ...

Patterns to investigate:
  - Carcharhinus perezi frequently confused with Carcharhinus acronotus (8 times)
```

This helps identify:
- Overall reliability of temporal proximity suggestions
- Species pairs that are visually similar (may need classifier training)
- False positive patterns (e.g., specific equipment/conditions)
