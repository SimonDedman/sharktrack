# New SSD Setup Guide

**Created:** October 6, 2025
**SSD Location:** `/media/simon/Extreme SSD/`
**Status:** Ready for clean pipeline execution

---

## 📊 Current State Summary

### **New SSD Status**
- **Capacity:** 1.9TB (74% used, 494GB free)
- **Mount:** `/media/simon/Extreme SSD/`
- **Status:** ✅ Clean - No worker folders, no converted_output_final artifacts

### **Video Inventory**
| Collection | Videos | Size | Status |
|-----------|--------|------|--------|
| BRUV_Summer_2022_1_45 | 257 | 880GB | ✅ Original format |
| BRUV_Summer_2022_46_62 | 102 (+28 .original) | 376GB | ⚠️ Needs cleanup + conversion |
| BRUV_Winter_2021_103_105 | 27 | 98GB | ✅ Original format |
| **Total** | **386** | **~1.35TB** | |

### **Issues to Address**
1. ⚠️ Remove 28 .original backup files (legacy from old SSD)
2. ✅ No converted_output_final folder (good)
3. ✅ No worker-based folders (good)
4. ✅ No analysis results yet (clean slate)

---

## 🚀 Quick Start - Complete Pipeline

### **Step 1: Cleanup (5 minutes)**

```bash
cd /home/simon/Installers/sharktrack-1.5

# Remove legacy .original files
find "/media/simon/Extreme SSD" -name "*.original" -delete

# Verify cleanup
find "/media/simon/Extreme SSD" -name "*.original" | wc -l
# Should output: 0

# Check final video count
find "/media/simon/Extreme SSD" -name "*.MP4" | wc -l
# Should output: 386
```

### **Step 2: Activate Virtual Environment**

```bash
source sharktrack-env/bin/activate

# Verify environment
python3 -c "import pandas; print('Environment OK')"
```

### **Step 3: Video Conversion (~2-3 hours)**

Only BRUV_Summer_2022_46_62 needs conversion:

```bash
# Convert BRUV 46-62 with --convert-replace (replaces originals)
python3 sharktrack.py convert \
  --input "/media/simon/Extreme SSD/BRUV_Summer_2022_46_62" \
  --convert-replace

# Expected output:
# - 102 videos converted
# - Originals replaced in-place
# - Space saved: ~200GB (60-75% compression)
# - Time: 2-3 hours
```

### **Step 4: ML Analysis (~6-8 hours)**

Run parallel analysis on all three collections:

```bash
# Analyze BRUV 1-45 (257 videos, already optimized)
python3 parallel_sharktrack_analysis.py \
  --input "/media/simon/Extreme SSD/BRUV_Summer_2022_1_45" \
  --output "/media/simon/Extreme SSD/analysis_results"

# Analyze BRUV 46-62 (102 videos, now converted)
python3 parallel_sharktrack_analysis.py \
  --input "/media/simon/Extreme SSD/BRUV_Summer_2022_46_62" \
  --output "/media/simon/Extreme SSD/analysis_results"

# Analyze Winter 2021 (27 videos)
python3 parallel_sharktrack_analysis.py \
  --input "/media/simon/Extreme SSD/BRUV_Winter_2021_103_105" \
  --output "/media/simon/Extreme SSD/analysis_results"

# Expected output:
# - analysis_results/ folder created in each BRUV directory
# - overview.csv files with detection data
# - Detection images organized by video
# - Auto-balancing: 7 workers (CPU: 12, RAM: 30.2GB)
# - Time: ~60 seconds per video × 386 videos = 6-8 hours
```

### **Step 5: Consolidate Results (~1 minute)**

```bash
# Create master CSV with all detections
python3 << 'EOF'
import pandas as pd
from pathlib import Path

# Find all overview.csv files
all_csvs = list(Path('/media/simon/Extreme SSD').rglob('overview.csv'))
print(f"Found {len(all_csvs)} CSV files")

# Load and concatenate
dfs = [pd.read_csv(csv) for csv in all_csvs]
combined = pd.concat(dfs, ignore_index=True)

# Save consolidated results
output_path = '/media/simon/Extreme SSD/analysis_results/consolidated_all.csv'
Path(output_path).parent.mkdir(parents=True, exist_ok=True)
combined.to_csv(output_path, index=False)

print(f"\n✅ Consolidation complete!")
print(f"   • CSV files processed: {len(all_csvs)}")
print(f"   • Total detections: {len(combined)}")
print(f"   • Output: {output_path}")

# Show species breakdown
if 'species' in combined.columns:
    print(f"\n📊 Species detected:")
    print(combined['species'].value_counts())
EOF
```

---

## 📁 Expected Final Directory Structure

```
/media/simon/Extreme SSD/
├── BRUV_Summer_2022_1_45/
│   ├── BRUV 1/
│   │   ├── GH018629.MP4          (original, ~3.7GB each)
│   │   ├── GH028629.MP4
│   │   └── analysis_results/
│   │       ├── GH018629/
│   │       │   └── internal_results/
│   │       │       └── overview.csv
│   │       └── GH028629/
│   ├── BRUV 2/
│   └── ...
│
├── BRUV_Summer_2022_46_62/
│   ├── BRUV 46/
│   │   ├── GH012490.MP4          (converted, ~0.9GB each)
│   │   ├── GH022490.MP4
│   │   └── analysis_results/
│   ├── BRUV 47/
│   └── ...
│
├── BRUV_Winter_2021_103_105/
│   ├── BRUV 103/
│   ├── BRUV 104/
│   └── BRUV 105/
│
└── analysis_results/
    └── consolidated_all.csv      (master CSV with all detections)
```

---

## 🔧 Active Scripts Reference

### **Primary Scripts (Production Ready)**

#### 1. **`parallel_sharktrack_analysis.py`** ⭐
- **Purpose:** Parallel ML analysis with auto-balancing workers
- **Features:**
  - Auto-detects optimal workers (7 on current system)
  - Real-time overwriting progress display
  - Results placed in original BRUV directories
  - Subprocess isolation for stability

#### 2. **`simple_batch_processor_v2.py`**
- **Purpose:** Simplified batch wrapper with preset modes
- **Presets:**
  - `--convert-replace` - Convert and replace originals (most common)
  - `--convert-only` - Convert but keep originals (safest)
  - `--analyze-only` - Skip conversion, analyze existing

### **Deprecated Scripts** (moved to `deprecated/` folder)
- ❌ `enhanced_batch_processor.py`
- ❌ `simple_batch_processor.py`
- ❌ `parallel_sharktrack_simple.py`
- ❌ `process_all_bruv_data.py`
- ❌ `demo_deletion_policy.py`
- ❌ `restore_converted_videos.py` (drive recovery only)
- ❌ `reorganize_analysis_results.py` (legacy cleanup only)
- ❌ Shell scripts

**See:** `deprecated/README.md` for details

---

## 📚 Documentation

### **Core Documentation**
- **`docs/01-core-system/PIPELINE_DOCUMENTATION.md`** - Complete pipeline guide (THIS IS THE MAIN DOC)
- **`docs/01-core-system/SETUP_AND_USAGE.md`** - Virtual environment and setup
- **`docs/01-core-system/BATCH_PROCESSOR_GUIDE.md`** - Batch processing guide
- **`deprecated/README.md`** - Deprecated scripts reference

### **Legacy Documentation** (archive/delete)
- `RESUME_AFTER_SSD_RECONNECT.md` - Old SSD recovery notes (no longer relevant)

---

## 🐛 Troubleshooting

### **Issue: "ModuleNotFoundError: No module named 'pandas'"**
```bash
# Ensure virtual environment is activated
source sharktrack-env/bin/activate

# Verify pandas is installed
python3 -c "import pandas; print(pandas.__version__)"
```

### **Issue: "FileNotFoundError: sharktrack.py not found"**
```bash
# Ensure you're in the correct directory
cd /home/simon/Installers/sharktrack-1.5

# Verify sharktrack.py exists
ls -la sharktrack.py
```

### **Issue: Progress bar not updating**
- This is normal - the parallel analysis uses overwriting progress display
- Wait for status updates (they appear every ~60 seconds per video)

### **Issue: "Out of memory" errors**
- Auto-balancing should prevent this (7 workers @ 4GB RAM each = 28GB)
- If it occurs, manually set workers: `--workers 5`

### **Issue: Videos look corrupted after conversion**
- Check compression ratios - should be 2-4:1 (3.7GB → 0.9-1.5GB)
- Ratios >10:1 indicate potential corruption
- Examples to verify (see PIPELINE_DOCUMENTATION.md):
  - GH019977.MP4: 2.4:1 ✅
  - GH065662.MP4: 1.8:1 ✅

---

## ⏱️ Time Estimates

| Phase | Task | Time |
|-------|------|------|
| 1 | Cleanup (.original files) | 5 min |
| 2 | Conversion (BRUV 46-62, 102 videos) | 2-3 hours |
| 3 | ML Analysis (386 videos @ 60s each) | 6-8 hours |
| 4 | Consolidation | 1 min |
| **Total** | **Complete pipeline** | **~8-11 hours** |

**Recommended:** Run overnight or during a long work session

---

## ✅ Success Criteria

After completing the pipeline, verify:

1. **Video counts:**
   ```bash
   find "/media/simon/Extreme SSD" -name "*.MP4" | wc -l
   # Should be: 386 (no .original files)
   ```

2. **Analysis results:**
   ```bash
   find "/media/simon/Extreme SSD" -name "overview.csv" | wc -l
   # Should be: 386 (one per video)
   ```

3. **Consolidated CSV:**
   ```bash
   ls -lh "/media/simon/Extreme SSD/analysis_results/consolidated_all.csv"
   # Should exist with >0 bytes
   ```

4. **Space savings:**
   ```bash
   du -sh "/media/simon/Extreme SSD"
   # Should be ~1.15TB (down from ~1.35TB after conversion)
   ```

---

## 🚨 Important Notes

### **Differences from Old SSD Workflow:**
1. ✅ Use `--convert-replace` from the start (no manual restoration needed)
2. ✅ No worker-based folders (results go directly to BRUV directories)
3. ✅ No .original files to manage (conversion replaces in-place)
4. ✅ Clean directory structure (no artifacts or duplicates)

### **What NOT to Do:**
- ❌ Don't use deprecated scripts from `deprecated/` folder
- ❌ Don't create `converted_output_final/` folder manually
- ❌ Don't run `restore_converted_videos.py` (not needed)
- ❌ Don't run `reorganize_analysis_results.py` (not needed)

### **Pipeline Differences:**
- **Old workflow:** Convert → Worker folders → Restore → Reorganize → Analyze
- **New workflow:** Convert with --replace → Analyze → Consolidate (3 steps vs 5)

---

## 📝 Next Steps After Pipeline Completion

1. **Verify results** - Check consolidated CSV for expected detections
2. **Archive old SSD data** - Old SSD can be wiped after verification
3. **Delete deprecated scripts** - Remove `deprecated/` folder
4. **Update documentation** - Mark pipeline as "complete" in docs
5. **Backup results** - Copy consolidated CSV to safe location

---

## 🔗 Quick Links

- **Main Documentation:** `docs/01-core-system/PIPELINE_DOCUMENTATION.md`
- **Setup Guide:** `docs/01-core-system/SETUP_AND_USAGE.md`
- **Deprecated Scripts:** `deprecated/README.md`
- **Project Root:** `/home/simon/Installers/sharktrack-1.5/`
- **New SSD:** `/media/simon/Extreme SSD/`

---

**Last Updated:** October 6, 2025
**Pipeline Status:** ✅ Ready to execute
**Expected Completion:** 8-11 hours total processing time
