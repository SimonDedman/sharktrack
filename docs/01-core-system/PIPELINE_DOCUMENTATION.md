# SharkTrack Pipeline Documentation

**Last Updated:** October 7, 2025
**Status:** Production Ready - Critical Path Fix Applied

---

## 📋 Table of Contents

1. [Critical Fixes Applied](#critical-fixes-applied)
2. [Current Production Pipeline](#current-production-pipeline)
3. [Active Scripts](#active-scripts)
4. [Deprecated Scripts](#deprecated-scripts)
5. [New SSD State](#new-ssd-state)
6. [Recommended Workflow](#recommended-workflow)

---

## Critical Fixes Applied

### **🔧 Fix #1: Dynamic SSD Path Resolution** (October 7, 2025)
**File:** `parallel_sharktrack_analysis.py:152-154`
**Issue:** Hardcoded old SSD path caused PermissionError when creating analysis directories
**Root Cause:** `find_original_video_directory()` had default `search_root="/media/simon/SSK SSD1/"`
**Impact:** All analysis jobs failed silently with permission errors

**Fix Applied:**
```python
# OLD (hardcoded):
original_video_dir = find_original_video_directory(video_file.name)  # defaults to /media/simon/SSK SSD1/

# NEW (dynamic):
search_root = str(video_file.parent.parent.parent)  # Derive from video path
original_video_dir = find_original_video_directory(video_file.name, search_root)
```

**Result:** Analysis now works on any SSD path, automatically detecting the correct root directory from input video location.

---

### **🔧 Fix #2: Output Directory Path Correction** (October 7, 2025)
**File:** `parallel_sharktrack_analysis.py:294-313`
**Issue:** Consolidation looking for CSVs directly in worker_output, but app.py writes to internal_results/ subdirectory
**Root Cause:** Incorrect assumption about app.py output structure
**Impact:** Consolidation reported "0 tracks found" despite successful video processing

**Fix Applied:**
```python
# OLD:
output_csv = worker_output / "output.csv"
overview_csv = worker_output / "overview.csv"

# NEW:
internal_results = worker_output / "internal_results"
output_csv = internal_results / "output.csv"
overview_csv = internal_results / "overview.csv"
```

**Result:** Consolidation now correctly reads detection data from internal_results/ subdirectory.

---

### **🔧 Fix #3: Subprocess Timeout Extension** (October 7, 2025)
**File:** `parallel_sharktrack_analysis.py:192`
**Issue:** 5-minute timeout too short for 60+ minute video processing
**Root Cause:** Default conservative timeout
**Impact:** Long videos killed mid-processing

**Fix Applied:**
```python
# OLD:
timeout=300  # 5 minutes

# NEW:
timeout=7200  # 2 hours per video
```

**Result:** Videos can now complete processing without timeout errors.

---

### **🔧 Fix #4: Enhanced Error Logging** (October 7, 2025)
**File:** `parallel_sharktrack_analysis.py:215-234`
**Issue:** Subprocess errors not visible, analysis failed silently
**Root Cause:** Minimal error output
**Impact:** Debugging required manual process inspection

**Fix Applied:**
```python
# Added detailed error reporting:
print(f"[{worker_id:>6}] STDERR: {error_msg}")
print(f"[{worker_id:>6}] STDOUT (last 200 chars): {stdout_msg[-200:]}")
import traceback
traceback.print_exc()
```

**Result:** Full error context now visible for debugging.

---

### **✅ Verification Results**

**Test Case:** Winter 2021 Collection (27 videos)
- ✅ All 27 videos processed successfully
- ✅ 2 tracks found in GP073799.MP4 (1 elasmobranch)
- ✅ Average processing time: 40.5 seconds per video
- ✅ Consolidation correctly aggregated results
- ✅ Results saved to: `/media/simon/Extreme SSD/analysis_results/consolidated/`

**Production Deployment:**
- 🟢 BRUV 1-45 (257 videos) running successfully
- 🟢 BRUV 46-62 (102 videos) running successfully
- ⏱️ Estimated completion: 2-3 hours with 7 parallel workers

---

## Current Production Pipeline

### **Phase 1: Data Preparation**
- **Input:** Raw BRUV videos on external SSD
- **Output:** Organized BRUV directory structure
- **Status:** ✅ Complete (data already organized)

### **Phase 2: Video Conversion**
- **Input:** Original 4K HEVC videos (~3.7GB each)
- **Process:** Convert to H.264 with optimized settings
- **Output:** Compressed videos (~0.9-1.5GB each, 60-75% size reduction)
- **Script:** `sharktrack.py convert --convert-replace`

### **Phase 3: ML Analysis**
- **Input:** Converted videos
- **Process:** YOLO object detection + BoT-SORT tracking
- **Output:** Detection CSVs with species, timestamps, bounding boxes
- **Script:** `parallel_sharktrack_analysis.py`

### **Phase 4: Results Consolidation**
- **Input:** Individual CSV files per video
- **Process:** Pandas consolidation
- **Output:** Single master CSV with all detections
- **Script:** Python pandas (inline)

---

## Active Scripts

### **🟢 PRODUCTION - Primary Pipeline**

#### 1. **`parallel_sharktrack_analysis.py`** ⭐ PRIMARY
**Purpose:** Parallel ML analysis with auto-balancing workers
**Created:** Sept 28, 2025
**Status:** ✅ Active - Production Ready
**Features:**
- Auto-detects optimal workers based on CPU/RAM
- Real-time overwriting progress display
- Places analysis results in original BRUV directories
- Subprocess isolation for stability
- Progress monitoring with ANSI escape sequences

**Usage:**
```bash
python3 parallel_sharktrack_analysis.py \
  --input "/media/simon/Extreme SSD/BRUV_Summer_2022_46_62" \
  --output "/media/simon/Extreme SSD/analysis_results"
```

**Key Improvements:**
- Fixed progress bar calculation (total work vs average workers)
- Eliminated worker-based folder artifacts
- Auto-balancing: 7 workers on current system (CPU: 12, RAM: 30.2GB)

---

#### 2. **`simple_batch_processor_v2.py`** ⭐ WRAPPER
**Purpose:** Simplified batch processor with preset modes
**Created:** Sept 27, 2025
**Status:** ✅ Active - Recommended for New Users
**Features:**
- 3 clear preset modes (--convert-only, --convert-replace, --analyze-only)
- Reduces 13 confusing parameters to simple presets
- Integrates deletion policy for space management

**Usage:**
```bash
# Convert and replace originals (most common):
python3 simple_batch_processor_v2.py --convert-replace ./BRUV_videos

# Convert but keep originals (safest):
python3 simple_batch_processor_v2.py --convert-only ./BRUV_videos ./output

# Just analyze existing converted videos:
python3 simple_batch_processor_v2.py --analyze-only ./converted_videos ./results
```

---

### **🟡 UTILITY - Cleanup & Organization**

#### 3. **`restore_converted_videos.py`**
**Purpose:** Move converted videos back to original BRUV directories
**Created:** Sept 29, 2025
**Status:** ⚠️ Utility - Use Only for Drive Recovery
**Features:**
- Finds original video locations across BRUV collections
- Creates .original backups before replacing
- Dry-run mode for read-only filesystems
- Handles I/O errors with accessible directory workaround

**Note:** This script was created to fix the corrupted drive workflow. With `--convert-replace` used from the start on new SSD, this script should NOT be needed.

---

#### 4. **`reorganize_analysis_results.py`**
**Purpose:** Reorganize analysis results from worker-based to BRUV-based structure
**Created:** Sept 28, 2025
**Status:** ⚠️ Utility - Use Only for Legacy Cleanup
**Features:**
- Moves results from ML_worker_* folders to proper BRUV directories
- Maps videos to their original BRUV locations
- Creates analysis_results subdirectories

**Note:** This script fixed the worker-based folder issue. With updated `parallel_sharktrack_analysis.py`, this is no longer needed for new processing.

---

### **🔴 DEPRECATED - Move to deprecated/ folder**

#### 5. **`enhanced_batch_processor.py`**
**Purpose:** Advanced BRUV processor with resumption and dynamic load balancing
**Created:** Sept 26, 2025
**Status:** ❌ Deprecated
**Reason:** Overcomplicated with dependencies on utils/ modules that don't exist. Replaced by `simple_batch_processor_v2.py`

**Dependencies (missing):**
- `utils.resumable_processor`
- `utils.dynamic_load_balancer`

---

#### 6. **`simple_batch_processor.py`**
**Purpose:** First attempt at simplified batch processing
**Created:** Sept 28, 2025
**Status:** ❌ Deprecated
**Reason:** Superseded by `simple_batch_processor_v2.py` with better preset modes

---

#### 7. **`parallel_sharktrack_simple.py`**
**Purpose:** Early parallel analysis prototype
**Created:** Sept 28, 2025
**Status:** ❌ Deprecated
**Reason:** Superseded by `parallel_sharktrack_analysis.py` with better progress monitoring and worker management

---

#### 8. **`test_parallel_simple.py`**
**Purpose:** Test script for parallel analysis
**Created:** Sept 28, 2025
**Status:** ❌ Deprecated
**Reason:** Testing script, no longer needed

---

#### 9. **`process_all_bruv_data.py`**
**Purpose:** Batch processor prototype
**Created:** Sept 26, 2025
**Status:** ❌ Deprecated
**Reason:** Early iteration, replaced by simplified batch processors

---

#### 10. **`demo_deletion_policy.py`**
**Purpose:** Demonstrates deletion policy logic
**Created:** Sept 26, 2025
**Status:** ❌ Deprecated
**Reason:** Demo/example code, integrated into main batch processors

---

#### 11. **`app_BKUP.py`** & **`app.py`**
**Purpose:** Web application interface
**Created:** April 8, 2025 (BKUP), Sept 26, 2025 (current)
**Status:** ⚠️ Keep for Future - Not part of batch pipeline
**Reason:** These are for the web interface, separate from batch processing pipeline

---

### **🔵 SHELL SCRIPTS**

#### 12. **`restore_videos_simple.sh`**
**Purpose:** Simple wrapper for video restoration
**Created:** Sept 28, 2025
**Status:** ❌ Deprecated
**Reason:** Wrapper for `restore_converted_videos.py`, not needed with clean workflow

---

#### 13. **`process_bruv_data.sh`**
**Purpose:** Shell wrapper for batch processing
**Created:** Sept 16, 2025
**Status:** ❌ Deprecated
**Reason:** Early shell-based approach, replaced by Python scripts

---

## New SSD State

**Location:** `/media/simon/Extreme SSD/`
**Capacity:** 1.9TB (74% used, 494GB free)
**Status:** ✅ Clean - Ready for fresh pipeline

### Current Data:
- **BRUV_Summer_2022_1_45**: 257 videos, 880GB
- **BRUV_Summer_2022_46_62**: 102 videos (+ 28 .original backups), 376GB
- **BRUV_Winter_2021_103_105**: 27 videos, 98GB
- **Total**: 386 videos, ~1.35TB

### Issues to Fix:
1. ⚠️ **28 .original backup files** in BRUV_Summer_2022_46_62 - should be removed
2. ✅ No `converted_output_final/` folder - good
3. ✅ No worker-based folders - good
4. ✅ No analysis results yet - clean slate

---

## Recommended Workflow

### **Step 1: Cleanup New SSD**
```bash
# Remove .original backups (legacy from old SSD)
find "/media/simon/Extreme SSD" -name "*.original" -delete

# Verify cleanup
find "/media/simon/Extreme SSD" -name "*.original" | wc -l  # Should be 0
```

### **Step 2: Video Conversion** (BRUV 46-62 only)
```bash
# Activate virtual environment
cd /home/simon/Installers/sharktrack-1.5
source sharktrack-env/bin/activate

# Convert BRUV 46-62 videos with --convert-replace
python3 sharktrack.py convert \
  --input "/media/simon/Extreme SSD/BRUV_Summer_2022_46_62" \
  --convert-replace

# Expected: 102 videos converted, originals replaced in-place
# Time: ~2-3 hours
```

### **Step 3: ML Analysis** (all collections)
```bash
# Analyze BRUV 1-45 (already optimized, no conversion needed)
python3 parallel_sharktrack_analysis.py \
  --input "/media/simon/Extreme SSD/BRUV_Summer_2022_1_45" \
  --output "/media/simon/Extreme SSD/analysis_results"

# Analyze BRUV 46-62 (now converted)
python3 parallel_sharktrack_analysis.py \
  --input "/media/simon/Extreme SSD/BRUV_Summer_2022_46_62" \
  --output "/media/simon/Extreme SSD/analysis_results"

# Analyze Winter collection
python3 parallel_sharktrack_analysis.py \
  --input "/media/simon/Extreme SSD/BRUV_Winter_2021_103_105" \
  --output "/media/simon/Extreme SSD/analysis_results"

# Expected: analysis_results/ folder in each BRUV directory
# Time: ~6-8 hours for all 386 videos
```

### **Step 4: Consolidate Results**
```bash
# Consolidate all CSV results into single master file
python3 << 'EOF'
import pandas as pd
from pathlib import Path

all_csvs = list(Path('/media/simon/Extreme SSD').rglob('overview.csv'))
print(f"Found {len(all_csvs)} CSV files")

dfs = [pd.read_csv(csv) for csv in all_csvs]
combined = pd.concat(dfs, ignore_index=True)

output_path = '/media/simon/Extreme SSD/analysis_results/consolidated_all.csv'
combined.to_csv(output_path, index=False)

print(f"Consolidated {len(all_csvs)} files")
print(f"Total detections: {len(combined)}")
print(f"Output: {output_path}")
EOF
```

---

## Script Deprecation Plan

### **Move to `deprecated/` folder:**
```bash
mkdir -p /home/simon/Installers/sharktrack-1.5/deprecated

mv enhanced_batch_processor.py deprecated/
mv simple_batch_processor.py deprecated/
mv parallel_sharktrack_simple.py deprecated/
mv test_parallel_simple.py deprecated/
mv process_all_bruv_data.py deprecated/
mv demo_deletion_policy.py deprecated/
mv restore_videos_simple.sh deprecated/
mv process_bruv_data.sh deprecated/
mv reorganize_analysis_results.py deprecated/
mv restore_converted_videos.py deprecated/
```

### **Keep in root:**
- `parallel_sharktrack_analysis.py` ⭐ PRIMARY
- `simple_batch_processor_v2.py` ⭐ WRAPPER
- `app.py` (web interface - future)
- `app_BKUP.py` (backup of web interface)

---

## Documentation Status

### **Current Documentation:**
- ✅ `docs/01-core-system/SETUP_AND_USAGE.md` - Virtual environment and workflow
- ✅ `docs/01-core-system/BATCH_PROCESSOR_GUIDE.md` - Batch processing guide
- ✅ `RESUME_AFTER_SSD_RECONNECT.md` - Legacy recovery notes
- ✅ `docs/01-core-system/PIPELINE_DOCUMENTATION.md` - This file

### **To Update:**
- `SETUP_AND_USAGE.md` - Update with new SSD paths
- `BATCH_PROCESSOR_GUIDE.md` - Focus on `simple_batch_processor_v2.py` only
- `RESUME_AFTER_SSD_RECONNECT.md` - Archive or delete (legacy from old SSD)

---

## Summary

**Active Pipeline (2 scripts):**
1. `parallel_sharktrack_analysis.py` - Primary ML analysis
2. `simple_batch_processor_v2.py` - Simplified batch wrapper

**Deprecated (10 scripts):**
- Move to `deprecated/` folder, delete on project completion

**Clean Workflow:**
1. Cleanup new SSD (remove .original files)
2. Convert BRUV 46-62 with `--convert-replace`
3. Run ML analysis on all collections
4. Consolidate results with pandas

**Expected Results:**
- 386 videos analyzed
- ~8-11 hours total processing time
- Clean directory structure with no artifacts
- Single consolidated CSV with all detections
