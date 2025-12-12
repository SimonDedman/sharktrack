# Teleost Detection Bootstrap Problem

## Overview

SharkTrack currently uses a YOLO-based **elasmobranch detector** trained specifically to detect sharks and rays. This creates a fundamental challenge when trying to extend the system to distinguish between true elasmobranch detections and false positives (teleosts, equipment, humans, etc.).

## The Problem

### Current Pipeline

1. **Detection Stage**: YOLO model scans video frames for objects that "look like sharks"
2. **Tracking Stage**: BoTSORT tracks detected objects across frames
3. **Classification Stage**: (planned) Classifier determines species or FALSE category

### The Bootstrap Dilemma

The current classifier training data (`class_mapping.txt`) includes:

```
0   Carcharhinus_acronotus
1   Carcharhinus_limbatus
2   Carcharhinus_perezi
3   FALSE_artifact
4   FALSE_equipment
5   FALSE_fish          <-- Problem: How do we get these?
6   FALSE_human
7   FALSE_other
8   FALSE_plant
9   Galeocerdo_cuvier
10  Ginglymostoma_cirratum
11  UNKNOWN_teleost     <-- Problem: How do we get these?
```

**The catch**: If the elasmobranch detector is good at its job, it won't detect teleosts (bony fish) in the first place. We can only train a classifier to recognize teleosts if the detector gives us teleost candidates - but an elasmobranch-specialized detector filters them out.

### Real Example

In BRUV 043 / GH062489, a barracuda (teleost) is clearly visible from 13:02 to 13:16. However:
- The elasmobranch detector did **not** detect it during this period
- Track 15 ended at 13:02 when the detector lost the object
- Track 16 started at 13:18 when a nurse shark entered the frame
- The barracuda was effectively invisible to the system

This is the correct behavior for a shark detector, but it means we cannot collect barracuda training data through the normal pipeline.

## Why This Matters

In BRUV videos, common sources of false positives include:

| Category | Examples | Frequency |
|----------|----------|-----------|
| FALSE_fish | Barracuda, large snapper, triggerfish | Common |
| FALSE_equipment | Chum box, bait arm, camera housing | Common |
| FALSE_human | Diver arms, swimmer shadows | Occasional |
| FALSE_artifact | Surface glare, bubbles, particles | Common |
| FALSE_plant | Sargassum, seagrass | Location-dependent |

If the detector reliably ignores these, we have no training data for them. But when the detector occasionally does flag them (edge cases, unusual angles), we need a classifier that can correctly label them as FALSE.

## Potential Solutions

### 1. Lower Detection Threshold (Current Approach)

**Strategy**: Use a lower confidence threshold (e.g., 0.3 instead of 0.5) to capture more marginal detections.

**Pros**:
- Simple to implement
- Captures edge cases where detector is uncertain

**Cons**:
- Generates many more false positives to review
- Still won't capture objects the detector confidently ignores
- Processing time increases significantly

### 2. General Object Detector + Classification

**Strategy**: Replace elasmobranch detector with a general "moving object" detector, then classify everything.

**Pros**:
- Would capture all potential objects of interest
- More comprehensive training data

**Cons**:
- Would detect every fish in every frame (massive processing load)
- Requires training/obtaining a general marine object detector
- Fundamentally changes the pipeline architecture

### 3. Two-Stage Hybrid Approach

**Strategy**:
1. Run elasmobranch detector for main analysis
2. Run separate "non-shark detector" on flagged time windows
3. Combine results for classifier training

**Pros**:
- Maintains efficient shark-focused detection
- Targeted capture of confusable species in relevant contexts

**Cons**:
- More complex pipeline
- Requires defining "flagged time windows"
- Needs second detector model

### 4. Active Learning / Hard Example Mining

**Strategy**:
1. Collect FALSE detections that slip through current detector
2. Periodically re-train detector to be more discriminative
3. Use rejected candidates as negative training examples

**Pros**:
- Continuous improvement
- Uses existing infrastructure

**Cons**:
- Slow to build training set
- Depends on detector making mistakes

### 5. External Data Augmentation

**Strategy**: Import teleost images from external datasets (e.g., iNaturalist, FishNet, academic databases).

**Pros**:
- Immediate access to labeled data
- Species-verified imagery

**Cons**:
- Different image quality/context than BRUV
- May not generalize well to underwater video
- Licensing considerations

## Current Implementation

As of December 2025, SharkTrack uses approach #1 (lower threshold) combined with #4 (collecting FALSE detections):

```python
# class_mapping.txt shows current training classes
# FALSE categories populated from manual validation
# Threshold set at 0.3 for reanalysis runs
```

The classifier training data (`CLASSIFIER_TRAINING_DATA/`) is organized by class:
- Species folders contain validated shark thumbnails
- FALSE_* folders contain validated non-shark thumbnails
- Data grows as users validate more detections

## Recommendations

### Short Term (Current Project)
- Continue collecting FALSE detections at current threshold
- Document which FALSE categories are underrepresented
- Consider running a subset of videos at very low threshold (0.1) specifically to mine hard negatives

### Medium Term (Platform Development)
- Investigate general object detection models (YOLOv8 with COCO weights)
- Develop "scene understanding" module to identify high-activity periods
- Create species confusion matrix from validation data

### Long Term (Platform Vision)
- Multi-model ensemble: specialized detector + general detector
- User feedback loop for continuous model improvement
- Federated learning across multiple BRUV deployments

## Related Documents

- [COLLECTIVE_SPECIES_INTELLIGENCE.md](COLLECTIVE_SPECIES_INTELLIGENCE.md) - Platform vision for species ID
- [PROJECT_VISION_INDEX.md](PROJECT_VISION_INDEX.md) - Overall platform roadmap
- `/home/simon/Documents/Si Work/PostDoc Work/Saving The Blue/Data/BRUV/CLASSIFIER_TRAINING_DATA/class_mapping.txt` - Current class definitions

## References

- BoTSORT paper: https://arxiv.org/abs/2206.14651
- YOLO detection thresholds: https://docs.ultralytics.com/
- Marine object detection challenges: Various literature on underwater CV
