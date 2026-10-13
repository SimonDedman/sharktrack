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
│  [video folders] ──► [utils/station_timeline.py] ──► chapters.csv +        │
│  [stable_durations.csv]                              station_level_durations.csv│
│                                                          │                  │
│  [validation_results.csv] + [output.csv] ──►  [build_station_level_maxn.py] │
│                                                          ▼                  │
│                         ┌─────────────────────────────────┐                │
│                         │  station_level_maxn.csv         │                │
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
| 7.1 | Build station timeline | `utils/station_timeline.py` (GUI: MaxN page, step 1) | Yes | video folders + settle times CSV | `chapters.csv`, `station_level_durations.csv`, `timeline_problems.csv` | ~100KB | PROJECT |
| 7.2 | Calculate station-level MaxN | `build_station_level_maxn.py` (GUI: MaxN page, step 2) | Yes | chapters.csv + durations + detection CSVs + validation CSVs | `station_level_maxn.csv` | ~50KB | PROJECT |

**Commands:**
```bash
python utils/station_timeline.py --collection NAME=/path/to/collection --settle-csv stable_durations.csv -o analysed/station_timeline
python build_station_level_maxn.py --maxn-csv analysed/station_timeline/chapters.csv \
    --durations-csv analysed/station_timeline/station_level_durations.csv \
    --detections output.csv --validations validation_results_XX.csv -o analysed/station_level_maxn.csv
```

Step 7.1 stops on chapter gaps, unreadable chapters (ffprobe cannot open them), several recordings in one station folder, and missing settle times. Those stations are left out of `station_level_durations.csv`, listed in `timeline_problems.csv`, and the command exits with status 2. `--allow-chapter-gaps` accepts gaps explicitly (the missing footage is then not on the clock).

**Output files:**
- `station_timeline/chapters.csv` - one row per chapter, with `chapter_offset_sec`
- `station_timeline/station_level_durations.csv` - one row per station
- `station_level_maxn.csv` - one row per station: `maxn_<taxon>`, `maxn_<species>`, window length, tracks in window

**Metrics calculated (station-level MaxN CSV):**

| Column | Description |
|--------|-------------|
| `maxn_shark`, `maxn_ray_skate`, `maxn_teleost`, `maxn_invertebrate`, `maxn_turtle`, `maxn_other` | Largest number of distinct true tracks of that taxon group in one frame, inside the window |
| `maxn_{species}` | The same per species (underscores for spaces) |
| `n_tracks_in_window` | Distinct true tracks inside the window |
| `analysis_window_min` | Window actually used: `--window-minutes`, cut short if the recording ends first |
| `deploy_sec`, `retrieve_sec`, `stable_duration_sec` | Settle times and stable length |

**Algorithm notes:**
- Only tracks marked `true_detection` in the validation CSVs count; species and taxon come from the same rows.
- A track is `(video_id, track_id)`. Track ids restart per video and collide across separate runs, so joining on `track_id` alone mixes species between runs and inflates MaxN.
- Station time = `chapter_offset_sec` + time in video. The window is `[deploy_sec, deploy_sec + window]` on that clock.
- MaxN is the maximum over frames of the count of distinct tracks, per taxon group and per species.
- `utils/compute_maxn.py` (upstream, thumbnail-rename labels, no window, no validation CSV) is legacy and is not part of this workflow.

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
| `station_level_maxn.csv` | Station-level MaxN | ~50KB | `analysed/` |
| `chapters.csv`, `station_level_durations.csv` | Station timeline tables | ~100KB | `analysed/station_timeline/` |

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
