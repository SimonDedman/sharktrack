#!/usr/bin/env python3
"""
A/B Test for thumbnail selection algorithms.

Generates multiple thumbnail variants using different frame selection strategies
for a sample of tracks, allowing visual comparison of approaches.
"""

import os
import sys
import cv2
import pandas as pd
import numpy as np
from pathlib import Path

# Configuration
TRACKS_CSV = "/home/simon/Documents/Si Work/PostDoc Work/Saving The Blue/Data/BRUV/REANALYSIS_QAQC_20251202/reanalysis_all_tracks.csv"
OUTPUT_DIR = "/home/simon/Documents/Si Work/PostDoc Work/Saving The Blue/Data/BRUV/REANALYSIS_QAQC_20251202/validation/ab_test"

# Video path mapping
VIDEO_ROOTS = {
    "Summer_2022_1_45": "/media/simon/Extreme SSD/BRUV_Summer_2022_1_45",
    "Summer_2022_46_62": "/media/simon/Extreme SSD/BRUV_Summer_2022_46_62",
    "Winter_2021_101_105": "/media/simon/Extreme SSD/BRUV_Winter_2021_101_105",
}


def get_video_path(collection, bruv_station, video_id):
    """Get full path to video file."""
    root = VIDEO_ROOTS.get(collection)
    if not root:
        return None

    bruv_num = bruv_station.replace("BRUV ", "").replace("BRUV", "")
    bruv_folder = f"BRUV {int(bruv_num)}"

    video_path = os.path.join(root, bruv_folder, f"{video_id}.MP4")
    if os.path.exists(video_path):
        return video_path
    return None


def extract_frame(video_path, frame_num, bbox, output_path, padding=50):
    """Extract a frame from video with bounding box crop."""
    try:
        cap = cv2.VideoCapture(video_path)
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
        ret, frame = cap.read()
        cap.release()

        if not ret or frame is None:
            return False

        h, w = frame.shape[:2]
        x1, y1, x2, y2 = bbox

        # Add padding
        x1 = max(0, int(x1) - padding)
        y1 = max(0, int(y1) - padding)
        x2 = min(w, int(x2) + padding)
        y2 = min(h, int(y2) + padding)

        crop = frame[y1:y2, x1:x2]

        if crop.size == 0:
            return False

        cv2.imwrite(output_path, crop, [cv2.IMWRITE_JPEG_QUALITY, 85])
        return True
    except Exception as e:
        print(f"Error extracting frame: {e}")
        return False


# =============================================================================
# SCORING STRATEGIES
# =============================================================================

def score_max_confidence(row, track_df, frame_width=1920):
    """Original strategy: just use confidence."""
    return row['confidence']


def score_center_weighted(row, track_df, frame_width=1920):
    """Prefer detections closer to frame center."""
    bbox_center_x = (row['xmin'] + row['xmax']) / 2
    frame_center = frame_width / 2

    # Distance from center, normalized to 0-1
    distance = abs(bbox_center_x - frame_center) / frame_center
    center_weight = 1 - distance  # 1 at center, 0 at edge

    return row['confidence'] * center_weight


def score_size_weighted(row, track_df, frame_width=1920):
    """Prefer larger bounding boxes (closer shark = more detail)."""
    bbox_width = row['xmax'] - row['xmin']
    bbox_height = row['ymax'] - row['ymin']
    bbox_area = bbox_width * bbox_height

    # Normalize by max area in track
    max_area = track_df.apply(lambda r: (r['xmax'] - r['xmin']) * (r['ymax'] - r['ymin']), axis=1).max()
    size_weight = bbox_area / max_area if max_area > 0 else 1

    return row['confidence'] * size_weight


def score_edge_penalty(row, track_df, frame_width=1920, frame_height=1080):
    """Penalize detections at frame edges (shark entering/exiting)."""
    margin = 100  # pixels from edge to penalize

    penalty = 1.0

    # Left edge
    if row['xmin'] < margin:
        penalty *= 0.7
    # Right edge
    if row['xmax'] > frame_width - margin:
        penalty *= 0.7
    # Top edge
    if row['ymin'] < margin:
        penalty *= 0.9
    # Bottom edge
    if row['ymax'] > frame_height - margin:
        penalty *= 0.9

    return row['confidence'] * penalty


def score_combined_v1(row, track_df, frame_width=1920, frame_height=1080):
    """Combined: confidence + center + edge penalty."""
    # Center weight
    bbox_center_x = (row['xmin'] + row['xmax']) / 2
    frame_center = frame_width / 2
    distance = abs(bbox_center_x - frame_center) / frame_center
    center_weight = 1 - (distance * 0.5)  # 1.0 at center, 0.5 at edge

    # Edge penalty
    margin = 100
    edge_penalty = 1.0
    if row['xmin'] < margin or row['xmax'] > frame_width - margin:
        edge_penalty = 0.7

    return row['confidence'] * center_weight * edge_penalty


def score_combined_v2(row, track_df, frame_width=1920, frame_height=1080):
    """Combined: confidence + center + size + edge penalty."""
    # Center weight
    bbox_center_x = (row['xmin'] + row['xmax']) / 2
    frame_center = frame_width / 2
    distance = abs(bbox_center_x - frame_center) / frame_center
    center_weight = 1 - (distance * 0.3)  # Lighter center preference

    # Size weight
    bbox_area = (row['xmax'] - row['xmin']) * (row['ymax'] - row['ymin'])
    max_area = track_df.apply(lambda r: (r['xmax'] - r['xmin']) * (r['ymax'] - r['ymin']), axis=1).max()
    size_weight = 0.5 + 0.5 * (bbox_area / max_area if max_area > 0 else 1)  # 0.5 to 1.0

    # Edge penalty
    margin = 150
    edge_penalty = 1.0
    if row['xmin'] < margin:
        edge_penalty *= 0.6
    if row['xmax'] > frame_width - margin:
        edge_penalty *= 0.6

    return row['confidence'] * center_weight * size_weight * edge_penalty


def score_combined_v3(row, track_df, frame_width=1920, frame_height=1080):
    """Combined v3: Strong edge penalty, moderate center/size preference."""
    # Center weight (gentler)
    bbox_center_x = (row['xmin'] + row['xmax']) / 2
    frame_center = frame_width / 2
    distance = abs(bbox_center_x - frame_center) / frame_center
    center_weight = 1 - (distance * 0.2)

    # Size weight
    bbox_area = (row['xmax'] - row['xmin']) * (row['ymax'] - row['ymin'])
    max_area = track_df.apply(lambda r: (r['xmax'] - r['xmin']) * (r['ymax'] - r['ymin']), axis=1).max()
    size_weight = 0.7 + 0.3 * (bbox_area / max_area if max_area > 0 else 1)

    # Strong edge penalty
    margin = 100
    edge_penalty = 1.0
    # How much of bbox is cut off at edge?
    if row['xmin'] < margin:
        cutoff = (margin - row['xmin']) / (row['xmax'] - row['xmin'])
        edge_penalty *= max(0.3, 1 - cutoff)
    if row['xmax'] > frame_width - margin:
        cutoff = (row['xmax'] - (frame_width - margin)) / (row['xmax'] - row['xmin'])
        edge_penalty *= max(0.3, 1 - cutoff)

    return row['confidence'] * center_weight * size_weight * edge_penalty


# All strategies to test
STRATEGIES = {
    'A_max_conf': score_max_confidence,
    'B_center': score_center_weighted,
    'C_size': score_size_weighted,
    'D_edge': score_edge_penalty,
    'E_combined_v1': score_combined_v1,
    'F_combined_v2': score_combined_v2,
    'G_combined_v3': score_combined_v3,
}


def select_best_frame(track_df, strategy_func):
    """Select best frame for a track using given strategy."""
    scores = []
    for idx, row in track_df.iterrows():
        score = strategy_func(row, track_df)
        scores.append((idx, score, row))

    best_idx, best_score, best_row = max(scores, key=lambda x: x[1])
    return best_row, best_score


def generate_ab_test(tracks_df, sample_tracks, output_dir):
    """Generate A/B test thumbnails for sample tracks."""
    os.makedirs(output_dir, exist_ok=True)
    thumb_dir = os.path.join(output_dir, "thumbnails")
    os.makedirs(thumb_dir, exist_ok=True)

    results = []

    for i, (collection, bruv, video, track_id) in enumerate(sample_tracks):
        print(f"\nProcessing track {i+1}/{len(sample_tracks)}: {bruv}/{video}/Track {track_id}")

        # Get all detections for this track
        track_df = tracks_df[
            (tracks_df['collection'] == collection) &
            (tracks_df['bruv_station'] == bruv) &
            (tracks_df['video_id'] == video) &
            (tracks_df['track_id'] == track_id)
        ].copy()

        if len(track_df) == 0:
            print(f"  No detections found!")
            continue

        video_path = get_video_path(collection, bruv, video)
        if not video_path:
            print(f"  Video not found!")
            continue

        print(f"  Found {len(track_df)} detections")

        track_result = {
            'collection': collection,
            'bruv_station': bruv,
            'video_id': video,
            'track_id': track_id,
            'num_detections': len(track_df),
            'video_path': video_path,
        }

        # Generate thumbnail for each strategy
        for strategy_name, strategy_func in STRATEGIES.items():
            best_row, score = select_best_frame(track_df, strategy_func)

            bruv_num = bruv.replace("BRUV ", "").zfill(3)
            thumb_filename = f"BRUV_{bruv_num}_{video}_{track_id}_{strategy_name}.jpg"
            thumb_path = os.path.join(thumb_dir, thumb_filename)

            bbox = (best_row['xmin'], best_row['ymin'], best_row['xmax'], best_row['ymax'])

            success = extract_frame(video_path, int(best_row['frame']), bbox, thumb_path)

            track_result[f'{strategy_name}_thumb'] = thumb_filename if success else None
            track_result[f'{strategy_name}_frame'] = best_row['frame']
            track_result[f'{strategy_name}_time'] = best_row['time']
            track_result[f'{strategy_name}_conf'] = best_row['confidence']
            track_result[f'{strategy_name}_score'] = score
            track_result[f'{strategy_name}_bbox_x'] = best_row['xmin']

            print(f"  {strategy_name}: frame {int(best_row['frame'])}, conf={best_row['confidence']:.3f}, score={score:.3f}, x={best_row['xmin']:.0f}")

        results.append(track_result)

    return pd.DataFrame(results)


def generate_comparison_html(results_df, output_dir):
    """Generate HTML page for visual comparison."""
    html = """<!DOCTYPE html>
<html>
<head>
    <title>Thumbnail Selection A/B Test</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #1a1a1a; color: #fff; }
        h1 { color: #3498db; }
        .track { margin-bottom: 40px; border: 1px solid #444; padding: 20px; border-radius: 8px; background: #2a2a2a; }
        .track-header { margin-bottom: 15px; }
        .strategies { display: flex; flex-wrap: wrap; gap: 15px; }
        .strategy {
            flex: 1;
            min-width: 250px;
            max-width: 350px;
            background: #333;
            padding: 10px;
            border-radius: 5px;
            text-align: center;
        }
        .strategy img {
            max-width: 100%;
            height: 200px;
            object-fit: contain;
            cursor: pointer;
            border-radius: 4px;
        }
        .strategy-name {
            font-weight: bold;
            color: #3498db;
            margin-bottom: 5px;
            font-size: 14px;
        }
        .strategy-info { font-size: 11px; color: #aaa; }
        .winner { border: 3px solid #27ae60; }
        #modal {
            display: none;
            position: fixed;
            top: 0; left: 0;
            width: 100%; height: 100%;
            background: rgba(0,0,0,0.9);
            z-index: 1000;
            cursor: pointer;
        }
        #modal img {
            max-width: 95%;
            max-height: 95%;
            position: absolute;
            top: 50%; left: 50%;
            transform: translate(-50%, -50%);
        }
        .legend {
            background: #333;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 20px;
        }
        .legend h3 { margin-top: 0; color: #3498db; }
        .legend ul { margin: 0; padding-left: 20px; }
        .legend li { margin: 5px 0; }
    </style>
</head>
<body>
    <h1>Thumbnail Selection A/B Test</h1>

    <div class="legend">
        <h3>Strategies Tested</h3>
        <ul>
            <li><b>A_max_conf</b>: Original - highest confidence frame (current method)</li>
            <li><b>B_center</b>: Prefer frames where shark is centered horizontally</li>
            <li><b>C_size</b>: Prefer frames with larger bounding box (closer shark)</li>
            <li><b>D_edge</b>: Penalize frames where shark is at frame edge</li>
            <li><b>E_combined_v1</b>: Confidence × center weight × edge penalty</li>
            <li><b>F_combined_v2</b>: Confidence × center × size × edge (balanced)</li>
            <li><b>G_combined_v3</b>: Strong edge penalty, moderate center/size</li>
        </ul>
    </div>

    <div id="tracks">
"""

    strategy_names = [k for k in STRATEGIES.keys()]

    for _, row in results_df.iterrows():
        html += f"""
        <div class="track">
            <div class="track-header">
                <h3>{row['bruv_station']} / {row['video_id']} / Track {row['track_id']}</h3>
                <p>Collection: {row['collection']} | Detections: {row['num_detections']}</p>
            </div>
            <div class="strategies">
"""

        for strategy in strategy_names:
            thumb = row.get(f'{strategy}_thumb')
            frame = row.get(f'{strategy}_frame', 'N/A')
            time = row.get(f'{strategy}_time', 'N/A')
            conf = row.get(f'{strategy}_conf', 0)
            score = row.get(f'{strategy}_score', 0)
            bbox_x = row.get(f'{strategy}_bbox_x', 0)

            if thumb:
                html += f"""
                <div class="strategy">
                    <div class="strategy-name">{strategy}</div>
                    <img src="thumbnails/{thumb}" onclick="showModal(this.src)" />
                    <div class="strategy-info">
                        Frame: {int(frame) if frame != 'N/A' else 'N/A'}<br>
                        Time: {time}<br>
                        Conf: {conf:.3f}<br>
                        Score: {score:.3f}<br>
                        BBox X: {bbox_x:.0f}
                    </div>
                </div>
"""

        html += """
            </div>
        </div>
"""

    html += """
    </div>

    <div id="modal" onclick="this.style.display='none'">
        <img id="modalImg" src="">
    </div>

    <script>
        function showModal(src) {
            document.getElementById('modalImg').src = src;
            document.getElementById('modal').style.display = 'block';
        }
    </script>
</body>
</html>
"""

    html_path = os.path.join(output_dir, "ab_test.html")
    with open(html_path, 'w') as f:
        f.write(html)

    print(f"\nHTML saved to: {html_path}")
    return html_path


def main():
    print("=" * 70)
    print("THUMBNAIL SELECTION A/B TEST")
    print("=" * 70)

    # Load tracks
    print(f"\nLoading tracks from: {TRACKS_CSV}")
    tracks_df = pd.read_csv(TRACKS_CSV)
    print(f"Loaded {len(tracks_df)} detections")

    # Select sample tracks for testing
    # Include the specific track mentioned, plus a variety of others
    sample_tracks = [
        # The specific track mentioned by user
        ("Summer_2022_46_62", "BRUV 056", "GH069978", 26),

        # Other tracks from same video for comparison
        ("Summer_2022_46_62", "BRUV 056", "GH069978", 0),
        ("Summer_2022_46_62", "BRUV 056", "GH069978", 8),
        ("Summer_2022_46_62", "BRUV 056", "GH069978", 12),

        # Tracks with many detections (long tracks)
        ("Summer_2022_1_45", "BRUV 003", "GH035650", 0),
        ("Summer_2022_1_45", "BRUV 003", "GH025650", 0),
        ("Summer_2022_1_45", "BRUV 049", "GH048643", 0),

        # Various other tracks for diversity
        ("Summer_2022_1_45", "BRUV 010", "GH039966", 0),
        ("Summer_2022_1_45", "BRUV 018", "GH045656", 0),
        ("Summer_2022_1_45", "BRUV 031", "GH042485", 0),
        ("Summer_2022_46_62", "BRUV 054", "GH048644", 0),
        ("Summer_2022_46_62", "BRUV 055", "GH065661", 0),
    ]

    print(f"\nTesting {len(sample_tracks)} tracks with {len(STRATEGIES)} strategies")
    print(f"Output directory: {OUTPUT_DIR}")

    # Generate thumbnails
    results_df = generate_ab_test(tracks_df, sample_tracks, OUTPUT_DIR)

    # Save results CSV
    results_csv = os.path.join(OUTPUT_DIR, "ab_test_results.csv")
    results_df.to_csv(results_csv, index=False)
    print(f"\nResults saved to: {results_csv}")

    # Generate comparison HTML
    html_path = generate_comparison_html(results_df, OUTPUT_DIR)

    print("\n" + "=" * 70)
    print("COMPLETE!")
    print(f"Open in browser: file://{html_path}")
    print("=" * 70)


if __name__ == "__main__":
    main()
