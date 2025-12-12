#!/usr/bin/env python3
"""
Prepare training data for species classifier.

Combines:
1. Tristan's original validation (VALIDATION_TEMPLATE_TG.csv)
2. New HTML validation results (validation_results.json)

Organizes images into class folders for training:
  training_data/
    G_cirratum/
    C_perezi/
    C_acronotus/
    FALSE_human/
    FALSE_equipment/
    FALSE_fish/
    ...
"""

import os
import json
import csv
import shutil
from pathlib import Path
from collections import defaultdict

# ============================================================================
# CONFIGURATION
# ============================================================================

# Data sources
TRISTAN_VALIDATION = "/home/simon/Documents/Si Work/PostDoc Work/Saving The Blue/Data/BRUV/SHARKTRACK_FINAL_RESULTS_20251111/validation/VALIDATION_TEMPLATE_TG.csv"
TRISTAN_THUMBNAILS = "/home/simon/Documents/Si Work/PostDoc Work/Saving The Blue/Data/BRUV/SHARKTRACK_FINAL_RESULTS_20251111/detection_thumbnails/all_thumbnails"

# Look for exported CSV (from HTML "Export CSV" button)
NEW_VALIDATION_DIR = "/home/simon/Documents/Si Work/PostDoc Work/Saving The Blue/Data/BRUV/REANALYSIS_QAQC_20251202/validation"
NEW_THUMBNAILS = "/home/simon/Documents/Si Work/PostDoc Work/Saving The Blue/Data/BRUV/REANALYSIS_QAQC_20251202/validation/thumbnails"

# Output
OUTPUT_DIR = "/home/simon/Documents/Si Work/PostDoc Work/Saving The Blue/Data/BRUV/CLASSIFIER_TRAINING_DATA"

# Class mapping for FALSE detections (normalize Tristan's notes)
FALSE_CATEGORY_MAP = {
    'surface human': 'FALSE_human',
    'human arm': 'FALSE_human',
    'human': 'FALSE_human',
    'chum box': 'FALSE_equipment',
    'box and surface': 'FALSE_equipment',
    'boat hull': 'FALSE_equipment',
    'barracuda': 'FALSE_fish',
    'snapper': 'FALSE_fish',
    'triggerfish': 'FALSE_fish',
    'unknown fish': 'FALSE_fish',
    'sargassum': 'FALSE_plant',
    'surface wave': 'FALSE_other',
}

# Normalize species names to standard format
SPECIES_NORMALIZE = {
    # Nurse shark variants
    'g. cirratum': 'Ginglymostoma_cirratum',
    'g__cirratum': 'Ginglymostoma_cirratum',
    'ginglymostoma cirratum': 'Ginglymostoma_cirratum',
    'ginglymostoma_cirratum': 'Ginglymostoma_cirratum',
    'nurse shark': 'Ginglymostoma_cirratum',

    # Reef shark variants
    'c. perezi': 'Carcharhinus_perezi',
    'c__perezi': 'Carcharhinus_perezi',
    'carcharhinus perezi': 'Carcharhinus_perezi',
    'caribbean reef shark': 'Carcharhinus_perezi',

    # Blacknose shark variants
    'c. acronotus': 'Carcharhinus_acronotus',
    'c__acronotus': 'Carcharhinus_acronotus',
    'carcharhinus acronotus': 'Carcharhinus_acronotus',
    'blacknose shark': 'Carcharhinus_acronotus',

    # Blacktip shark variants
    'c. limbatus': 'Carcharhinus_limbatus',
    'carcharhinus limbatus': 'Carcharhinus_limbatus',
    'blacktip shark': 'Carcharhinus_limbatus',

    # Tiger shark variants
    'galeocerdo cuvier': 'Galeocerdo_cuvier',
    'tiger shark': 'Galeocerdo_cuvier',

    # FALSE categories - normalize case
    'human': 'FALSE_human',
    'bruv': 'FALSE_equipment',
    'boat': 'FALSE_equipment',
    'artifact': 'FALSE_artifact',
}

# ============================================================================
# FUNCTIONS
# ============================================================================

def sanitize_class_name(name):
    """Convert species/category name to valid folder name, normalizing variants."""
    # First normalize known variants
    name_lower = name.lower().strip()
    if name_lower in SPECIES_NORMALIZE:
        return SPECIES_NORMALIZE[name_lower]

    # Otherwise just sanitize
    return name.replace(' ', '_').replace('.', '_').replace('/', '_')


def load_tristan_validation():
    """Load Tristan's validated labels."""
    labels = []

    with open(TRISTAN_VALIDATION, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            filename = row['image_filename']
            true_detection = row['true_detection']
            species = row['species']
            notes = row['notes'].lower() if row['notes'] else ''

            if true_detection == 'TRUE' and species:
                class_name = sanitize_class_name(species)
            elif true_detection == 'FALSE':
                # Map FALSE notes to categories
                class_name = 'FALSE_other'
                for key, val in FALSE_CATEGORY_MAP.items():
                    if key in notes:
                        class_name = val
                        break
            else:
                continue

            src_path = os.path.join(TRISTAN_THUMBNAILS, filename)
            if os.path.exists(src_path):
                labels.append({
                    'source': 'tristan',
                    'filename': filename,
                    'src_path': src_path,
                    'class': class_name,
                })

    return labels


def load_new_validation():
    """Load new HTML validation results from exported CSV."""
    labels = []

    # Find exported CSV files (named validation_results_YYYY-MM-DD.csv)
    import glob
    csv_files = glob.glob(os.path.join(NEW_VALIDATION_DIR, "validation_results_*.csv"))

    if not csv_files:
        print(f"  No exported CSV found in: {NEW_VALIDATION_DIR}")
        print(f"  (Click 'Export CSV' in the validation HTML to create one)")
        return labels

    # Use most recent export
    csv_file = sorted(csv_files)[-1]
    print(f"  Loading: {os.path.basename(csv_file)}")

    with open(csv_file, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # CSV columns: thumbnail, collection, bruv_station, video_id, track_id,
            #              time, time_seconds, video_path, confidence,
            #              true_detection, taxon_group, species, notes

            true_detection = row.get('true_detection', '').strip().lower()
            group = row.get('taxon_group', '').strip()
            species = row.get('species', '').strip()
            thumbnail = row.get('thumbnail', '').strip()

            if not true_detection or not thumbnail:
                continue

            # Find thumbnail file
            thumb_path = os.path.join(NEW_THUMBNAILS, thumbnail)
            if not os.path.exists(thumb_path):
                continue

            if true_detection == 'true':
                if species:
                    class_name = sanitize_class_name(species)
                elif group:
                    class_name = f"UNKNOWN_{sanitize_class_name(group)}"
                else:
                    class_name = "UNKNOWN_elasmobranch"
            elif true_detection == 'false':
                # For FALSE detections, use species if available, else group
                label = species if species else group
                if label:
                    # Check if already normalized to a FALSE_ class
                    normalized = sanitize_class_name(label)
                    if normalized.startswith('FALSE_'):
                        class_name = normalized
                    else:
                        class_name = f"FALSE_{normalized}"
                else:
                    class_name = "FALSE_other"
            else:
                continue

            labels.append({
                'source': 'new_validation',
                'filename': thumbnail,
                'src_path': thumb_path,
                'class': class_name,
            })

    return labels


def organize_training_data(labels):
    """Organize images into class folders."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    class_counts = defaultdict(int)
    errors = []

    for item in labels:
        class_dir = os.path.join(OUTPUT_DIR, item['class'])
        os.makedirs(class_dir, exist_ok=True)

        dst_path = os.path.join(class_dir, item['filename'])

        try:
            if not os.path.exists(dst_path):
                shutil.copy2(item['src_path'], dst_path)
            class_counts[item['class']] += 1
        except Exception as e:
            errors.append(f"{item['filename']}: {e}")

    return class_counts, errors


def main():
    print("=" * 70)
    print("SPECIES CLASSIFIER TRAINING DATA PREPARATION")
    print("=" * 70)
    print()

    # Load Tristan's validation
    print("Loading Tristan's validation data...")
    tristan_labels = load_tristan_validation()
    print(f"  Found {len(tristan_labels)} labeled images")

    # Load new validation
    print("\nLoading new HTML validation data...")
    new_labels = load_new_validation()
    print(f"  Found {len(new_labels)} labeled images")

    # Combine
    all_labels = tristan_labels + new_labels
    print(f"\nTotal: {len(all_labels)} labeled images")

    if len(all_labels) == 0:
        print("\nNo labeled data found! Please complete some validation first.")
        return

    # Organize into folders
    print(f"\nOrganizing into: {OUTPUT_DIR}")
    class_counts, errors = organize_training_data(all_labels)

    # Summary
    print("\n" + "=" * 70)
    print("CLASS DISTRIBUTION")
    print("=" * 70)

    for class_name, count in sorted(class_counts.items(), key=lambda x: -x[1]):
        print(f"  {class_name}: {count}")

    print(f"\nTotal classes: {len(class_counts)}")
    print(f"Total images: {sum(class_counts.values())}")

    if errors:
        print(f"\nErrors ({len(errors)}):")
        for e in errors[:10]:
            print(f"  {e}")

    # Save class mapping
    class_mapping_path = os.path.join(OUTPUT_DIR, "class_mapping.txt")
    with open(class_mapping_path, 'w') as f:
        for i, class_name in enumerate(sorted(class_counts.keys())):
            f.write(f"{i}\t{class_name}\n")
    print(f"\nClass mapping saved to: {class_mapping_path}")

    print("\n" + "=" * 70)
    print("READY FOR TRAINING")
    print("=" * 70)
    print(f"\nTo train the classifier, run:")
    print(f"  python utils/train_species_classifier.py --data {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
