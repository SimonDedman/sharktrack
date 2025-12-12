"""
Deployment/Retrieval Detection for BRUV Videos
Detects unstable periods (deployment/retrieval) using background motion analysis
"""

import cv2
import numpy as np
from typing import Tuple, List, Optional


class DeploymentDetector:
    """
    Detects deployment and retrieval phases in BRUV videos by analyzing
    background stability and camera motion.
    """

    def __init__(self, stability_threshold: float = 0.15, min_stable_duration: int = 10):
        """
        Args:
            stability_threshold: Motion threshold (0-1). Higher = more lenient. Default 0.15
            min_stable_duration: Minimum seconds of stability to consider "deployed". Default 10s
        """
        self.stability_threshold = stability_threshold
        self.min_stable_duration = min_stable_duration

    def analyze_video_stability(self, video_path: str, sample_rate: int = 1) -> Tuple[int, int, List[float]]:
        """
        Analyze entire video to detect stable recording period.

        Args:
            video_path: Path to video file
            sample_rate: Analyze every Nth second (default 1 = every second)

        Returns:
            Tuple of (start_frame, end_frame, motion_scores)
            - start_frame: First frame of stable period
            - end_frame: Last frame of stable period
            - motion_scores: List of motion scores for visualization
        """
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        if fps == 0 or total_frames == 0:
            print(f"Warning: Could not read video properties for {video_path}")
            return 0, total_frames, []

        frame_skip = int(fps * sample_rate)
        motion_scores = []
        frame_indices = []

        prev_frame = None
        frame_idx = 0

        print(f"Analyzing video stability (sampling every {sample_rate}s)...")

        while frame_idx < total_frames:
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
            ret, frame = cap.read()

            if not ret:
                break

            # Convert to grayscale and resize for speed
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            small = cv2.resize(gray, (320, 180), interpolation=cv2.INTER_AREA)

            if prev_frame is not None:
                # Compute frame difference
                motion_score = self._compute_motion_score(prev_frame, small)
                motion_scores.append(motion_score)
                frame_indices.append(frame_idx)

            prev_frame = small
            frame_idx += frame_skip

        cap.release()

        if len(motion_scores) == 0:
            print("Warning: No motion scores computed")
            return 0, total_frames, []

        # Find stable period
        start_frame, end_frame = self._find_stable_period(
            motion_scores, frame_indices, fps, sample_rate
        )

        print(f"  Detected stable period: {start_frame/fps:.1f}s to {end_frame/fps:.1f}s")
        print(f"  Recommended skip_start: {start_frame/fps:.1f}s")
        print(f"  Recommended skip_end: {(total_frames - end_frame)/fps:.1f}s")

        return start_frame, end_frame, motion_scores

    def _compute_motion_score(self, prev_frame: np.ndarray, curr_frame: np.ndarray) -> float:
        """
        Compute normalized motion score between two frames.

        Returns:
            float: Motion score between 0 (stable) and 1 (high motion)
        """
        # Frame difference
        diff = cv2.absdiff(prev_frame, curr_frame)

        # Threshold to get binary motion mask
        _, motion_mask = cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)

        # Calculate percentage of pixels with motion
        motion_pixels = np.count_nonzero(motion_mask)
        total_pixels = motion_mask.size
        motion_ratio = motion_pixels / total_pixels

        # Also consider magnitude of change
        mean_diff = np.mean(diff)
        max_diff = np.max(diff)

        # Combined score (weighted average)
        score = (motion_ratio * 0.6) + (mean_diff / 255.0 * 0.3) + (max_diff / 255.0 * 0.1)

        return float(score)

    def _find_stable_period(self, motion_scores: List[float], frame_indices: List[int],
                           fps: float, sample_rate: int) -> Tuple[int, int]:
        """
        Find the longest continuous stable period in the video.

        Returns:
            Tuple of (start_frame, end_frame)
        """
        if len(motion_scores) == 0:
            return 0, 0

        # Smooth motion scores with moving average
        window_size = min(5, len(motion_scores))
        smoothed = np.convolve(motion_scores, np.ones(window_size)/window_size, mode='same')

        # Find stable regions (below threshold)
        is_stable = smoothed < self.stability_threshold

        # Find continuous stable periods
        stable_periods = []
        start_idx = None

        for i, stable in enumerate(is_stable):
            if stable and start_idx is None:
                start_idx = i
            elif not stable and start_idx is not None:
                duration = (i - start_idx) * sample_rate
                if duration >= self.min_stable_duration:
                    stable_periods.append((start_idx, i))
                start_idx = None

        # Handle case where video ends during stable period
        if start_idx is not None:
            duration = (len(is_stable) - start_idx) * sample_rate
            if duration >= self.min_stable_duration:
                stable_periods.append((start_idx, len(is_stable)))

        if not stable_periods:
            # No stable period found, return middle section as best guess
            print("  Warning: No stable period detected, using middle 80% of video")
            total_duration = len(frame_indices)
            margin = int(total_duration * 0.1)
            return frame_indices[margin], frame_indices[-margin] if len(frame_indices) > margin else frame_indices[-1]

        # Find longest stable period
        longest_period = max(stable_periods, key=lambda p: p[1] - p[0])
        start_idx, end_idx = longest_period

        # Convert indices back to frame numbers
        start_frame = frame_indices[start_idx]
        end_frame = frame_indices[end_idx - 1] if end_idx < len(frame_indices) else frame_indices[-1]

        return start_frame, end_frame

    def should_skip_frame(self, frame_number: int, fps: float, start_frame: int, end_frame: int) -> bool:
        """
        Determine if a frame should be skipped based on stable period.

        Args:
            frame_number: Current frame number
            fps: Video FPS
            start_frame: First frame of stable period
            end_frame: Last frame of stable period

        Returns:
            bool: True if frame should be skipped
        """
        return frame_number < start_frame or frame_number > end_frame

    def get_skip_times(self, video_path: str) -> Tuple[float, float]:
        """
        Get skip times in seconds for command line usage.

        Returns:
            Tuple of (skip_start_seconds, skip_end_seconds)
        """
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        cap.release()

        if fps == 0 or total_frames == 0:
            print(f"Warning: Could not read video, returning no skip times")
            return 0.0, 0.0

        start_frame, end_frame, _ = self.analyze_video_stability(video_path)

        skip_start = start_frame / fps if fps > 0 else 0.0
        skip_end = (total_frames - end_frame) / fps if fps > 0 else 0.0

        return skip_start, skip_end


def analyze_deployment_batch(video_paths: List[str], output_file: Optional[str] = None) -> dict:
    """
    Analyze multiple videos and generate skip recommendations.

    Args:
        video_paths: List of video file paths
        output_file: Optional CSV file to save results

    Returns:
        dict: Mapping of video_path -> (skip_start, skip_end)
    """
    detector = DeploymentDetector()
    results = {}

    for video_path in video_paths:
        print(f"\nAnalyzing: {video_path}")
        try:
            skip_start, skip_end = detector.get_skip_times(video_path)
            results[video_path] = (skip_start, skip_end)
        except Exception as e:
            print(f"  Error: {e}")
            results[video_path] = (0, 0)

    # Save to CSV if requested
    if output_file:
        import pandas as pd
        df = pd.DataFrame([
            {
                'video_path': path,
                'skip_start_seconds': times[0],
                'skip_end_seconds': times[1]
            }
            for path, times in results.items()
        ])
        df.to_csv(output_file, index=False)
        print(f"\nResults saved to: {output_file}")

    return results


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python deployment_detector.py <video_path>")
        sys.exit(1)

    video_path = sys.argv[1]
    detector = DeploymentDetector()
    skip_start, skip_end = detector.get_skip_times(video_path)

    print(f"\nRecommended settings:")
    print(f"  --skip_start {skip_start:.1f}")
    print(f"  --skip_end {skip_end:.1f}")
