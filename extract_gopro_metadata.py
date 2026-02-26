#!/usr/bin/env python3
"""
Extract GoPro camera metadata for all videos in FINAL_MaxN_all_BRUVs.csv.

Extracts ~16 gopro_ columns per video:
  Header (ffprobe + exiftool): duration, fps, resolution, codec, file_size,
    creation_time, firmware, camera_model, camera_serial, lens_serial,
    field_of_view, auto_rotation
  Frame analysis (OpenCV): water_clarity, light_level, substrate_auto,
    substrate_confidence

Checkpoints after each video to gopro_metadata_checkpoint.csv so re-runs
resume where they left off. Final output written to both a standalone
gopro_metadata_extracted.csv and merged into the FINAL_MaxN CSV.
"""

import json
import os
import subprocess
import sys
import time
from pathlib import Path

import cv2
import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

BRUV_DIR = Path("/home/simon/Documents/Si Work/PostDoc Work/Saving The Blue/Data/BRUV")
FINAL_MAXN_PATH = BRUV_DIR / "FINAL_MaxN_all_BRUVs.csv"

NAS_ROOT = Path("/run/user/1000/gvfs/smb-share:server=nas.local,share=usbshare1")

# Mapping: collection name in CSV -> (NAS subfolder, folder pattern)
# folder pattern: "BRUV {N}" or "{N}" where N is station_number
COLLECTION_MAP = {
    "Summer_2022_1_45": ("BRUV_Summer_2022_1_45", "BRUV {N}"),
    "Summer_2022_46_62": ("BRUV_Summer_2022_46_62", "BRUV {N}"),
    "Winter_2021_103_105": ("BRUV_Winter_2021_103_105", "BRUV {N}"),
    "BRUVs_March_Dec_2025": ("BRUVs_March 2023 and Dec 2025", "{N}"),
}

CHECKPOINT_PATH = Path("gopro_metadata_checkpoint.csv")
OUTPUT_PATH = Path("gopro_metadata_extracted.csv")

# Timeouts in seconds
FFPROBE_TIMEOUT = 30
EXIFTOOL_TIMEOUT = 30
FRAME_TIMEOUT = 120

# Columns produced by this script
GOPRO_COLUMNS = [
    "gopro_duration_sec", "gopro_duration_min", "gopro_fps", "gopro_resolution", "gopro_codec",
    "gopro_file_size_mb", "gopro_creation_time", "gopro_firmware",
    "gopro_camera_model", "gopro_camera_serial", "gopro_lens_serial",
    "gopro_field_of_view", "gopro_auto_rotation",
    "gopro_water_clarity", "gopro_light_level",
    "gopro_substrate_auto", "gopro_substrate_confidence",
]


# ---------------------------------------------------------------------------
# Path resolution
# ---------------------------------------------------------------------------

def resolve_video_path(row: pd.Series) -> Path | None:
    """Map a FINAL_MaxN row to the actual video file on the NAS."""
    collection = row["collection"]
    station_number = int(row["station_number"])
    video_id = row["video_id"]

    if collection not in COLLECTION_MAP:
        return None

    subfolder, pattern = COLLECTION_MAP[collection]
    bruv_folder = pattern.replace("{N}", str(station_number))
    video_file = f"{video_id}.MP4"

    path = NAS_ROOT / subfolder / bruv_folder / video_file
    if path.exists():
        return path

    # Try uppercase/lowercase variations
    for ext in [".mp4", ".MP4", ".Mp4"]:
        alt = NAS_ROOT / subfolder / bruv_folder / f"{video_id}{ext}"
        if alt.exists():
            return alt

    return None


# ---------------------------------------------------------------------------
# Header metadata extraction
# ---------------------------------------------------------------------------

def extract_ffprobe_metadata(video_path: Path) -> dict:
    """Extract metadata via ffprobe (duration, fps, resolution, codec, creation_time)."""
    result = {}
    try:
        cmd = [
            "ffprobe", "-v", "quiet", "-print_format", "json",
            "-show_format", "-show_streams", str(video_path),
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=FFPROBE_TIMEOUT)
        if proc.returncode != 0:
            return result

        data = json.loads(proc.stdout)

        # Format-level info
        fmt = data.get("format", {})
        dur_sec = round(float(fmt.get("duration", 0)), 2)
        result["gopro_duration_sec"] = dur_sec
        result["gopro_duration_min"] = round(dur_sec / 60, 2)
        file_size_bytes = int(fmt.get("size", 0))
        result["gopro_file_size_mb"] = round(file_size_bytes / (1024 * 1024), 2)

        # Creation time from format tags
        tags = fmt.get("tags", {})
        for key in ["creation_time", "date", "com.apple.quicktime.creationdate"]:
            if key in tags:
                result["gopro_creation_time"] = tags[key]
                break

        # Video stream info
        for stream in data.get("streams", []):
            if stream.get("codec_type") == "video":
                w = int(stream.get("width", 0))
                h = int(stream.get("height", 0))
                result["gopro_resolution"] = f"{w}x{h}"
                result["gopro_codec"] = stream.get("codec_name", "")

                # FPS from r_frame_rate (e.g. "30000/1001")
                fps_str = stream.get("r_frame_rate", "0/1")
                try:
                    num, den = fps_str.split("/")
                    result["gopro_fps"] = round(float(num) / float(den), 2)
                except (ValueError, ZeroDivisionError):
                    result["gopro_fps"] = 0
                break

    except (subprocess.TimeoutExpired, json.JSONDecodeError, Exception) as e:
        print(f"  ffprobe error: {e}")

    return result


def extract_exiftool_metadata(video_path: Path) -> dict:
    """Extract GoPro-specific metadata via exiftool."""
    result = {}
    try:
        cmd = [
            "exiftool", "-j",
            "-Model", "-SerialNumber", "-LensSerialNumber",
            "-FOV", "-FieldOfView", "-AutoRotation",
            "-FirmwareVersion", "-Software",
            str(video_path),
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=EXIFTOOL_TIMEOUT)
        if proc.returncode != 0:
            return result

        data = json.loads(proc.stdout)
        if not data:
            return result

        info = data[0]

        result["gopro_camera_model"] = info.get("Model", "")
        result["gopro_camera_serial"] = info.get("SerialNumber", "")
        result["gopro_lens_serial"] = info.get("LensSerialNumber", "")

        # Field of view - try multiple tag names
        fov = info.get("FOV", info.get("FieldOfView", ""))
        result["gopro_field_of_view"] = str(fov) if fov else ""

        result["gopro_auto_rotation"] = info.get("AutoRotation", "")

        # Firmware
        fw = info.get("FirmwareVersion", info.get("Software", ""))
        result["gopro_firmware"] = str(fw) if fw else ""

    except (subprocess.TimeoutExpired, json.JSONDecodeError, Exception) as e:
        print(f"  exiftool error: {e}")

    return result


# ---------------------------------------------------------------------------
# Frame analysis (reuses logic from utils/metadata_extractor.py)
# ---------------------------------------------------------------------------

def estimate_water_clarity(frames: list[np.ndarray]) -> float:
    """Estimate water clarity/visibility (0-1) via Laplacian variance."""
    scores = []
    for frame in frames:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        lap = cv2.Laplacian(gray, cv2.CV_64F)
        scores.append(min(lap.var() / 1000.0, 1.0))
    return round(float(np.mean(scores)), 4) if scores else float("nan")


def estimate_light_level(frames: list[np.ndarray]) -> float:
    """Estimate light level (0-1) via LAB L channel."""
    levels = []
    for frame in frames:
        lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
        levels.append(lab[:, :, 0].mean() / 255.0)
    return round(float(np.mean(levels)), 4) if levels else float("nan")


def classify_substrate(frames: list[np.ndarray]) -> tuple[str, float]:
    """Classify substrate from bottom 30% of frames."""
    votes = {"sand": 0, "rock": 0, "coral": 0, "seagrass": 0, "unknown": 0}
    for frame in frames:
        h = frame.shape[0]
        bottom = frame[int(h * 0.7):, :]
        hsv = cv2.cvtColor(bottom, cv2.COLOR_BGR2HSV)
        mean_hue = hsv[:, :, 0].mean()
        mean_sat = hsv[:, :, 1].mean()
        gray_bottom = cv2.cvtColor(bottom, cv2.COLOR_BGR2GRAY)
        tex_var = gray_bottom.std()

        if mean_sat < 50 and tex_var < 30:
            votes["sand"] += 1
        elif 40 < mean_hue < 80 and mean_sat > 80:
            votes["seagrass"] += 1
        elif tex_var > 60:
            votes["rock"] += 1
        elif mean_sat > 60 and mean_hue < 30:
            votes["coral"] += 1
        else:
            votes["unknown"] += 1

    best = max(votes, key=votes.get)
    conf = votes[best] / len(frames) if frames else 0
    return best, round(conf, 4)


def extract_frame_metadata(video_path: Path) -> dict:
    """Sample 11 evenly-spaced frames, discard first, analyze remaining 10."""
    result = {}
    try:
        cap = cv2.VideoCapture(str(video_path))
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        if frame_count < 2:
            cap.release()
            return result

        indices = np.linspace(0, frame_count - 1, 11, dtype=int)
        frames = []
        for idx in indices:
            cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
            ret, frame = cap.read()
            if ret:
                frames.append(frame)
        cap.release()

        # Discard first frame (deployment/boat)
        if len(frames) > 1:
            frames = frames[1:]

        if not frames:
            return result

        result["gopro_water_clarity"] = estimate_water_clarity(frames)
        result["gopro_light_level"] = estimate_light_level(frames)
        substrate, conf = classify_substrate(frames)
        result["gopro_substrate_auto"] = substrate
        result["gopro_substrate_confidence"] = conf

    except Exception as e:
        print(f"  frame analysis error: {e}")

    return result


# ---------------------------------------------------------------------------
# Per-video extraction
# ---------------------------------------------------------------------------

def extract_one_video(video_path: Path) -> dict:
    """Extract all gopro_ columns for a single video file."""
    row = {}

    # Header metadata (fast)
    row.update(extract_ffprobe_metadata(video_path))
    row.update(extract_exiftool_metadata(video_path))

    # Frame analysis (slower)
    try:
        frame_data = extract_frame_metadata(video_path)
        row.update(frame_data)
    except Exception as e:
        print(f"  frame analysis failed (NaN for frame columns): {e}")

    return row


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    if not NAS_ROOT.exists():
        print(f"ERROR: NAS not mounted at {NAS_ROOT}")
        print("Mount the NAS first, then re-run.")
        sys.exit(1)

    if not FINAL_MAXN_PATH.exists():
        print(f"ERROR: FINAL_MaxN CSV not found at {FINAL_MAXN_PATH}")
        sys.exit(1)

    print(f"Reading {FINAL_MAXN_PATH}")
    df = pd.read_csv(FINAL_MAXN_PATH)
    print(f"  {len(df)} rows, {len(df.columns)} columns")

    # Build composite key for joining (handles duplicate video_ids across collections)
    df["_key"] = df["collection"] + "|" + df["video_id"]

    # Load checkpoint if it exists
    done_keys = set()
    checkpoint_rows = []
    if CHECKPOINT_PATH.exists():
        cp = pd.read_csv(CHECKPOINT_PATH)
        cp["_key"] = cp["collection"] + "|" + cp["video_id"]
        done_keys = set(cp["_key"])
        checkpoint_rows = cp.to_dict("records")
        print(f"  Resuming: {len(done_keys)} videos already extracted")

    # Resolve paths and extract
    total = len(df)
    skipped = 0
    not_found = 0
    errors = 0

    for i, (_, row) in enumerate(df.iterrows()):
        key = row["_key"]
        vid = row["video_id"]
        collection = row["collection"]

        if key in done_keys:
            skipped += 1
            continue

        video_path = resolve_video_path(row)
        if video_path is None:
            print(f"[{i+1}/{total}] {vid} ({collection}) — FILE NOT FOUND, skipping")
            not_found += 1
            # Write a row with NaN for all gopro columns so we don't retry
            cp_row = {"collection": collection, "video_id": vid}
            for col in GOPRO_COLUMNS:
                cp_row[col] = float("nan") if col not in ("gopro_substrate_auto",) else ""
            checkpoint_rows.append(cp_row)
            done_keys.add(key)
            _save_checkpoint(checkpoint_rows)
            continue

        t0 = time.time()
        try:
            metadata = extract_one_video(video_path)
        except Exception as e:
            print(f"[{i+1}/{total}] {vid} — ERROR: {e}")
            errors += 1
            metadata = {}

        elapsed = time.time() - t0

        # Build summary line
        model = metadata.get("gopro_camera_model", "?")
        res = metadata.get("gopro_resolution", "?")
        fps = metadata.get("gopro_fps", "?")
        clarity = metadata.get("gopro_water_clarity", "?")
        print(f"[{i+1}/{total}] {vid} — {model}, {res}, {fps}fps, clarity={clarity} ({elapsed:.1f}s)")

        cp_row = {"collection": collection, "video_id": vid}
        cp_row.update(metadata)
        checkpoint_rows.append(cp_row)
        done_keys.add(key)

        # Checkpoint after each file
        _save_checkpoint(checkpoint_rows)

    # Write standalone output
    result_df = pd.DataFrame(checkpoint_rows)
    result_df.to_csv(OUTPUT_PATH, index=False)
    print(f"\nStandalone metadata: {OUTPUT_PATH} ({len(result_df)} rows)")

    # Merge into FINAL_MaxN
    _merge_into_final_maxn(df, result_df)

    print(f"\nDone. Skipped={skipped}, not_found={not_found}, errors={errors}")


def _save_checkpoint(rows: list[dict]):
    """Save checkpoint CSV."""
    pd.DataFrame(rows).to_csv(CHECKPOINT_PATH, index=False)


def _merge_into_final_maxn(df: pd.DataFrame, metadata_df: pd.DataFrame):
    """Left-join gopro_ columns onto FINAL_MaxN and save."""
    # Ensure metadata has the key
    if "_key" not in metadata_df.columns:
        metadata_df["_key"] = metadata_df["collection"] + "|" + metadata_df["video_id"]

    # Select only gopro_ columns + key for merging
    merge_cols = ["_key"] + [c for c in metadata_df.columns if c.startswith("gopro_")]
    meta_merge = metadata_df[merge_cols].copy()

    # Drop any existing gopro_ columns from df to avoid _x/_y suffixes
    existing_gopro = [c for c in df.columns if c.startswith("gopro_")]
    if existing_gopro:
        df = df.drop(columns=existing_gopro)

    merged = df.merge(meta_merge, on="_key", how="left")
    merged = merged.drop(columns=["_key"])

    # Write backup first
    backup_path = FINAL_MAXN_PATH.with_name("FINAL_MaxN_all_BRUVs_BACKUP_pre_gopro.csv")
    if not backup_path.exists():
        import shutil
        shutil.copy2(FINAL_MAXN_PATH, backup_path)
        print(f"  Backup saved: {backup_path}")

    merged.to_csv(FINAL_MAXN_PATH, index=False)
    print(f"  Updated {FINAL_MAXN_PATH} ({len(merged)} rows, {len(merged.columns)} columns)")


if __name__ == "__main__":
    main()
