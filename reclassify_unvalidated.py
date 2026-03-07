#!/usr/bin/env python3
"""
Reclassify unvalidated tracks using the species classifier.

Crops detections from existing thumbnails (full-frame images) using bbox
data from a tracks CSV, then runs the classifier on each crop.

Outputs updated validation CSV with new_prediction and new_confidence columns.
Checkpoints after each batch so it can resume if interrupted.

Must be run from the sharktrack project directory (so that utils/ is importable).
"""

import argparse
import csv
import os
import json
import gc
from collections import Counter

import cv2
import pandas as pd
import torch

from utils.species_classifier import SpeciesClassifier


def parse_args():
    parser = argparse.ArgumentParser(
        description="Reclassify unvalidated tracks from thumbnail crops.",
        epilog="""Examples:
  python reclassify_unvalidated.py \\
    --validation-csv data/validation_results.csv \\
    --tracks-csv data/tracks_for_validation.csv \\
    --thumbnails-dir thumbnails/

  python reclassify_unvalidated.py \\
    --validation-csv data/validation_results.csv \\
    --tracks-csv data/tracks_for_validation.csv \\
    --thumbnails-dir thumbnails/ \\
    --force-cpu --batch-size 100 -o reclassified.csv
""",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--validation-csv", required=True, help="Path to validation results CSV")
    parser.add_argument("--tracks-csv", required=True, help="Path to tracks CSV with bbox data (xmin/ymin/xmax/ymax/w/h)")
    parser.add_argument("--thumbnails-dir", required=True, help="Path to thumbnail images directory")
    parser.add_argument("--classifier", default="models/species_classifiers/stb_classifier", help="Path to species classifier (default: %(default)s)")
    parser.add_argument("-o", "--output", default="validation_reclassified.csv", help="Output CSV path (default: %(default)s)")
    parser.add_argument("--checkpoint", default="reclassify_checkpoint.json", help="Checkpoint file path (default: %(default)s)")
    parser.add_argument("--batch-size", type=int, default=50, help="Checkpoint interval (default: %(default)s)")
    parser.add_argument("--force-cpu", action="store_true", help="Force CPU inference (disable CUDA)")
    return parser.parse_args()


def load_best_detections(tracks_csv):
    print(f"Loading bbox data from {tracks_csv}...")
    best = {}
    with open(tracks_csv) as f:
        for r in csv.DictReader(f):
            key = (r['bruv_station'], r['video_id'], r['track_id'])
            conf = float(r['confidence'])
            if key not in best or conf > best[key]['conf']:
                best[key] = {
                    'conf': conf,
                    'xmin': float(r['xmin']),
                    'ymin': float(r['ymin']),
                    'xmax': float(r['xmax']),
                    'ymax': float(r['ymax']),
                    'w': int(r['w']),
                    'h': int(r['h']),
                }
    print(f"  Loaded bboxes for {len(best)} tracks")
    return best


def load_checkpoint(checkpoint_file):
    if os.path.exists(checkpoint_file):
        with open(checkpoint_file) as f:
            data = json.load(f)
        print(f"  Resuming from checkpoint: {len(data['completed'])} tracks done")
        return data
    return {'completed': {}, 'total_processed': 0}


def save_checkpoint(checkpoint, checkpoint_file):
    with open(checkpoint_file, 'w') as f:
        json.dump(checkpoint, f)


def classify_from_thumbnail(classifier, thumb_path, bbox_info):
    img = cv2.imread(thumb_path)
    if img is None:
        return None, 0.0

    sy = img.shape[0] / bbox_info['h']
    sx = img.shape[1] / bbox_info['w']
    x1 = max(0, int(bbox_info['xmin'] * sx))
    y1 = max(0, int(bbox_info['ymin'] * sy))
    x2 = min(img.shape[1], int(bbox_info['xmax'] * sx))
    y2 = min(img.shape[0], int(bbox_info['ymax'] * sy))

    crop = img[y1:y2, x1:x2]
    if crop.size == 0:
        return None, 0.0

    fake_row = pd.Series({
        'xmin': 0, 'ymin': 0,
        'xmax': crop.shape[1], 'ymax': crop.shape[0]
    })
    try:
        confidence, species = classifier(fake_row, crop)
        return species, confidence
    except Exception as e:
        print(f"  Classification error: {e}")
        return None, 0.0


def main():
    args = parse_args()

    if args.force_cpu:
        os.environ['CUDA_VISIBLE_DEVICES'] = ''

    print("=" * 70)
    print("RECLASSIFY UNVALIDATED TRACKS")
    print("=" * 70)

    checkpoint = load_checkpoint(args.checkpoint)

    print(f"\nLoading validation CSV: {args.validation_csv}")
    with open(args.validation_csv) as f:
        rows = list(csv.DictReader(f))
    fieldnames = list(rows[0].keys())

    total = len(rows)
    unvalidated = [r for r in rows if not r.get('true_detection', '').strip()]
    already_done = len(checkpoint['completed'])
    print(f"  Total tracks: {total}")
    print(f"  Unvalidated: {len(unvalidated)}")
    print(f"  Already reclassified: {already_done}")

    best_detections = load_best_detections(args.tracks_csv)

    print(f"\nLoading classifier: {args.classifier}")
    classifier = SpeciesClassifier.build_species_classifier(args.classifier)
    print(f"  Classes: {classifier.classes}")
    print(f"  Device: {classifier.device}")

    processed = 0
    skipped = 0
    results = {}

    print(f"\nClassifying {len(unvalidated) - already_done} remaining tracks...")
    print()

    for i, row in enumerate(unvalidated):
        track_key = f"{row['bruv_station']}|{row['video_id']}|{row['track_id']}"

        if track_key in checkpoint['completed']:
            results[track_key] = checkpoint['completed'][track_key]
            continue

        thumb_name = row.get('thumbnail', '')
        thumb_path = os.path.join(args.thumbnails_dir, thumb_name)
        if not os.path.exists(thumb_path):
            skipped += 1
            continue

        bbox_key = (row['bruv_station'], row['video_id'], row['track_id'])
        if bbox_key not in best_detections:
            skipped += 1
            continue

        species, confidence = classify_from_thumbnail(
            classifier, thumb_path, best_detections[bbox_key]
        )

        result = {
            'species': species,
            'confidence': round(confidence, 4)
        }
        results[track_key] = result
        checkpoint['completed'][track_key] = result
        processed += 1

        if processed % 10 == 0:
            pct = (already_done + processed) / len(unvalidated) * 100
            print(f"  {already_done + processed}/{len(unvalidated)} ({pct:.0f}%) - "
                  f"last: {species or 'below threshold'} ({confidence:.2f})")

        if processed % args.batch_size == 0:
            save_checkpoint(checkpoint, args.checkpoint)
            gc.collect()

    save_checkpoint(checkpoint, args.checkpoint)

    print(f"\nWriting output: {args.output}")
    with open(args.output, 'w', newline='') as f:
        out_fields = fieldnames.copy()
        if 'new_prediction' not in out_fields:
            out_fields.append('new_prediction')
        if 'new_confidence' not in out_fields:
            out_fields.append('new_confidence')

        writer = csv.DictWriter(f, fieldnames=out_fields)
        writer.writeheader()

        for row in rows:
            track_key = f"{row['bruv_station']}|{row['video_id']}|{row['track_id']}"
            if track_key in results:
                row['new_prediction'] = results[track_key]['species'] or ''
                row['new_confidence'] = results[track_key]['confidence']
            else:
                row['new_prediction'] = ''
                row['new_confidence'] = ''
            writer.writerow(row)

    print(f"\n{'=' * 70}")
    print("SUMMARY")
    print(f"{'=' * 70}")
    print(f"  Processed: {processed}")
    print(f"  Previously done: {already_done}")
    print(f"  Skipped (no thumb/bbox): {skipped}")
    print(f"  Total reclassified: {already_done + processed}")

    species_counts = Counter()
    for r in results.values():
        sp = r['species'] or 'below_threshold'
        species_counts[sp] += 1

    print(f"\nNew prediction distribution:")
    for sp, count in species_counts.most_common():
        print(f"  {sp:40s} {count:5d}")

    print(f"\nOutput saved to: {args.output}")
    print(f"Checkpoint at: {args.checkpoint}")
    print("\nDone! You can delete the checkpoint file if results look good.")


if __name__ == "__main__":
    main()
