# SharkTrack Analysis Pipeline - Complete Guide

**Created:** 2025-10-26
**Status:** Ready to Run (Awaiting Manual Validation)

---

## What You Have Now

### ✅ Completed

1. **Video Processing (100% Complete)**
   - 385 BRUV videos processed
   - 2,703 elasmobranch detections
   - 21 unique individual tracks
   - Location: `/media/simon/Extreme SSD/`

2. **Consolidated Database**
   - All detections in single CSV file
   - Environmental metadata integrated (88.6%)
   - SQLite database with indices
   - Location: `consolidated_results/`

3. **Analysis Scripts Created**
   - 4 complete Python scripts for standard BRUV analyses
   - Master run script for all analyses
   - Complete documentation
   - Location: `analysis_scripts/`

### ⏳ Next Steps (Your Action Required)

1. **Run Initial Analyses** (15 minutes)
2. **Manual Validation** (2-4 hours)
3. **Species Identification** (4-8 hours)
4. **Re-run Analyses** (15 minutes)
5. **Finalize Methods Section** (1-2 hours)

---

## How to Use the Analysis Pipeline

### STEP 1: Run Analyses (Do This Now!)

Open a terminal and run:

```bash
cd /home/simon/Installers/sharktrack-1.5/analysis_scripts
./run_all_analyses.sh
```

**What this does:**
- Calculates MaxN (relative abundance) for all videos
- Analyzes depth and temperature preferences
- Creates interactive and static distribution maps
- Generates draft Methods section for publication

**Time required:** ~5 minutes

**Outputs:**
- 20+ analysis files in `../analysis_results/`
- Plots, statistics, maps, and publication text

---

### STEP 2: Review the Results

After running the analyses, review:

**📊 Key Statistics:**
```
analysis_results/maxn_analysis/maxn_summary.json
```

**📈 Visualizations:**
```
analysis_results/maxn_analysis/maxn_distributions.png
analysis_results/environmental_analysis/depth_temperature_analysis.png
analysis_results/distribution_maps/detection_distribution_map.png
```

**🗺️ Interactive Maps:**
Open in web browser:
```
analysis_results/distribution_maps/interactive_detection_map.html
analysis_results/distribution_maps/detection_heatmap.html
```

**📝 Publication Draft:**
```
analysis_results/publication_materials/METHODS_SECTION.txt
```

---

### STEP 3: Manual Validation (Your Next Task)

**Goal:** Verify detection accuracy and identify species

**Process:**

1. **Review Detection Images**
   - Navigate to: `/media/simon/Extreme SSD/BRUV_XX/analysis_results/GHXXXXXX/internal_results/`
   - Each detection has a thumbnail image (e.g., `0-elasmobranch.jpg`)

2. **Start with High-Activity Videos**
   - Check `analysis_results/maxn_analysis/maxn_by_station.csv`
   - Top stations by activity:
     - BRUV 52: 988 detections
     - BRUV 38: 397 detections
     - BRUV 56: 231 detections

3. **Validate Detections**
   For each detection, determine:
   - ✅ True Positive (correct detection)
   - ❌ False Positive (incorrect detection)
   - ? False Negative (missed animal)

4. **Calculate Accuracy Metrics**
   - **Precision** = True Positives / (True Positives + False Positives)
   - **Recall** = True Positives / (True Positives + False Negatives)
   - Target: At least 50-100 validated detections for robust estimate

5. **Identify Species**
   Common Bahamas elasmobranchs:
   - Nurse shark (*Ginglymostoma cirratum*)
   - Lemon shark (*Negaprion brevirostris*)
   - Caribbean reef shark (*Carcharhinus perezi*)
   - Southern stingray (*Hypanus americanus*)
   - Yellow stingray (*Urobatis jamaicensis*)
   - Spotted eagle ray (*Aetobatus narinari*)

**Create Validation Spreadsheet:**

| Video ID | Detection | True/False | Species | Notes |
|----------|-----------|------------|---------|-------|
| GH049966 | 0-elasmobranch.jpg | True | Nurse shark | Clear view |
| GH015652 | 1-elasmobranch.jpg | True | Southern stingray | Partial view |
| ... | ... | ... | ... | ... |

---

### STEP 4: Update Database with Species IDs

After species identification, update the database:

```python
import pandas as pd

# Load database
df = pd.read_csv('consolidated_results/sharktrack_all_detections_with_metadata.csv')

# Example: Update specific detections
# (You'll create a mapping from your validation spreadsheet)

species_mapping = {
    'GH049966': 'Nurse shark',
    'GH015652': 'Southern stingray',
    # ... add all your identifications
}

# Update labels based on video ID
for video_id, species in species_mapping.items():
    df.loc[df['video_id'] == video_id, 'label'] = species

# Save updated database
df.to_csv('consolidated_results/sharktrack_all_detections_with_metadata.csv', index=False)
```

---

### STEP 5: Re-run Analyses with Validated Data

```bash
cd /home/simon/Installers/sharktrack-1.5/analysis_scripts
./run_all_analyses.sh
```

**Now you'll get:**
- Species-specific MaxN values
- Environmental preferences by species
- Species distribution maps
- Updated Methods section with species list

---

### STEP 6: Finalize Methods Section

1. Open: `analysis_results/publication_materials/METHODS_SECTION.txt`

2. Fill in all `[SPECIFY]` placeholders:
   - Geographic details (which islands/areas)
   - Exact camera model (e.g., "GoPro Hero 9")
   - Bait details (type and mass)
   - Survey months/seasons
   - Distance between stations

3. Add validation statistics:
   ```
   Precision: XX%
   Recall: XX%
   Species identified: [list]
   ```

4. Review checklist:
   `analysis_results/publication_materials/METHODS_CHECKLIST.md`

---

## File Locations Quick Reference

### Input Data
```
consolidated_results/
└── sharktrack_all_detections_with_metadata.csv  ← Main database
```

### Scripts
```
analysis_scripts/
├── 01_calculate_maxn.py              ← MaxN analysis
├── 02_depth_temperature_analysis.py   ← Environmental analysis
├── 03_distribution_maps.py            ← Spatial mapping
├── 04_generate_methods_section.py     ← Methods text
├── run_all_analyses.sh                ← Run everything
└── README.md                          ← Detailed documentation
```

### Outputs
```
analysis_results/
├── maxn_analysis/           ← Relative abundance
├── environmental_analysis/  ← Depth/temp preferences
├── distribution_maps/       ← Spatial patterns
└── publication_materials/   ← Methods section
```

### Detection Images (for validation)
```
/media/simon/Extreme SSD/
└── BRUV_Summer_2022_XX/
    └── BRUV XX/
        └── analysis_results/
            └── GHXXXXXX/
                └── internal_results/
                    ├── 0-elasmobranch.jpg  ← Thumbnail
                    └── output.csv          ← Detection data
```

---

## Expected Timeline

| Task | Time Required | Status |
|------|---------------|--------|
| Run initial analyses | 15 min | ⏳ Ready |
| Review results | 30 min | ⏳ After step 1 |
| Manual validation (50-100 detections) | 2-4 hours | ⏳ Your work |
| Species identification | 4-8 hours | ⏳ Your work |
| Update database | 30 min | ⏳ Script provided |
| Re-run analyses | 15 min | ⏳ Automated |
| Finalize Methods | 1-2 hours | ⏳ Fill placeholders |
| **TOTAL** | **~8-16 hours** | |

---

## Tips for Manual Validation

### Efficient Workflow

1. **Use two monitors** - Image on one, spreadsheet on other
2. **Work in batches** - Do 10-20 at a time, take breaks
3. **Prioritize high-confidence detections first** - Filter by confidence > 0.8
4. **Keep identification guides handy**
5. **Take notes on ambiguous cases** - Can discuss with colleagues

### What to Look For

**True Positive Indicators:**
- Clear shark/ray body shape
- Visible fins, tail, or distinctive features
- Appropriate size and proportion
- Consistent across multiple frames

**False Positive Indicators:**
- Diver/equipment
- Fish that isn't an elasmobranch
- Shadows or image artifacts
- Partial view of non-target species

**Species ID Clues:**
- Body shape (streamlined vs. flattened)
- Color pattern (spots, stripes, solid)
- Fin shape and position
- Size relative to bait arm
- Behavior (bottom-dwelling vs. swimming)

---

## Common Questions

### "Do I need to validate ALL 2,703 detections?"

**No.** A statistically valid sample is sufficient:
- Minimum: 50-100 detections
- Recommended: 200-300 detections
- Ideal: 500+ detections

Random sampling ensures representative accuracy estimate.

### "Can I identify just to genus level?"

**Yes, if species ID is uncertain:**
- "Carcharhinus sp." (genus)
- "Elasmobranch (unidentified)"
- "Ray sp."

Be consistent and note ID confidence.

### "What if videos have no metadata?"

The 307 detections without metadata (Winter 2021) can still be analyzed, just without environmental context. They're still valid for MaxN if species can be identified.

### "Should I re-train the model after validation?"

**Good question!** If you find systematic false positives/negatives, retraining could improve performance. But for publication of THIS dataset, validation is sufficient.

---

## Deliverables for Publication

After completing all steps, you'll have:

### Required for Methods Section
- [x] Detection precision and recall
- [x] Species list with scientific names
- [x] Environmental data summary
- [x] Statistical test results
- [x] All parameter values

### Required for Results Section
- [x] MaxN by species and habitat
- [x] Environmental preference statistics
- [x] Spatial distribution patterns
- [x] Habitat associations

### Required for Figures
- [x] Distribution map (Figure 1)
- [x] MaxN by habitat (Figure 2)
- [x] Depth/temperature analysis (Figure 3)
- [x] [Add others as needed]

### Supplementary Materials
- [x] Complete detection database (CSV)
- [x] Station locations (GeoJSON)
- [x] Analysis code (GitHub repo)

---

## Getting Help

### Script Documentation
- Each script has detailed comments
- `analysis_scripts/README.md` - Full documentation
- Run with `python3 script_name.py --help` (if implemented)

### Project Documentation
- `consolidated_results/PROJECT_COMPLETION_REPORT.md` - Overall project status
- `docs/SHARKTRACK_PROJECT_SUMMARY_AND_STRATEGIC_ANALYSIS.md` - Strategic analysis

### Data Issues
- Check `consolidated_results/summary_statistics.json` for data overview
- Review `consolidated_results/SUMMARY_REPORT_WITH_METADATA.md`

---

## Next Actions (Priority Order)

1. **TODAY:**
   ```bash
   cd /home/simon/Installers/sharktrack-1.5/analysis_scripts
   ./run_all_analyses.sh
   ```

2. **THIS WEEK:**
   - Review all generated plots and statistics
   - Select videos for manual validation
   - Create validation spreadsheet

3. **NEXT 2 WEEKS:**
   - Complete manual validation (50-100 detections minimum)
   - Identify species from detection images
   - Update database with species labels

4. **FOLLOWING WEEK:**
   - Re-run analyses with species data
   - Finalize Methods section
   - Begin Results section

5. **MONTH 2:**
   - Complete manuscript
   - Submit to journal

---

## Success Criteria

You'll know you're ready to submit when:

- ✅ Precision ≥ 70% (preferably ≥ 80%)
- ✅ Recall ≥ 60% (preferably ≥ 70%)
- ✅ Species identified for ≥ 80% of detections
- ✅ Methods section complete (no `[SPECIFY]` placeholders)
- ✅ All figures publication-quality
- ✅ Statistical tests reported with p-values
- ✅ Data deposited in repository (Zenodo, Dryad, GitHub)

---

## Questions Before You Start?

Review:
1. `analysis_scripts/README.md` - Detailed script documentation
2. `consolidated_results/PROJECT_COMPLETION_REPORT.md` - Full project status
3. This file - Overall workflow

Then **run the analyses** and see what you get!

---

*Ready to start? Run the analysis pipeline now:*

```bash
cd /home/simon/Installers/sharktrack-1.5/analysis_scripts
./run_all_analyses.sh
```

*Good luck! 🦈📊*
