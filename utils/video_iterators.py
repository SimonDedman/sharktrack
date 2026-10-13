import cv2
import av
import av.datasets
import os
import subprocess
import tempfile


def validate_video_readable(video_path, test_frames=100):
    """
    Test if a video can be read sequentially by OpenCV.

    GoPro videos with metadata streams (timecode, telemetry) often cause
    OpenCV's ffmpeg backend to fail after 10-20 frames.

    Args:
        video_path: Path to video file
        test_frames: Number of frames to test reading

    Returns:
        tuple: (is_readable: bool, frames_read: int, total_frames: int)
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return False, 0, 0

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    frames_to_test = min(test_frames, total_frames)

    frames_read = 0
    for i in range(frames_to_test):
        ret, _ = cap.read()
        if ret:
            frames_read += 1
        else:
            break

    cap.release()

    # Consider readable if we got at least 90% of test frames
    is_readable = frames_read >= frames_to_test * 0.9
    return is_readable, frames_read, total_frames


def reformat_video_for_opencv(video_path, output_dir=None):
    """
    Reformat a GoPro video to strip metadata streams that cause OpenCV issues.

    Uses ffmpeg to copy only the video stream, removing audio and data streams
    that can cause read failures.

    Args:
        video_path: Path to original video
        output_dir: Directory for reformatted video. If None, creates 'converted'
                    subdirectory next to the video.

    Returns:
        str: Path to reformatted video
    """
    video_dir = os.path.dirname(video_path)
    video_name = os.path.basename(video_path)

    if output_dir is None:
        output_dir = os.path.join(video_dir, 'converted')

    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, video_name)

    if os.path.exists(output_path):
        # Verify the converted file is readable
        is_readable, frames_read, _ = validate_video_readable(output_path, test_frames=50)
        if is_readable:
            return output_path
        else:
            # Converted file is corrupt, remove and recreate
            os.remove(output_path)

    # Use ffmpeg to strip non-video streams
    # -map 0:v selects only video stream
    # -c copy does stream copy (fast, no re-encoding)
    cmd = [
        'ffmpeg', '-y', '-i', video_path,
        '-map', '0:v',  # Only video stream
        '-c', 'copy',   # Stream copy (no re-encoding)
        output_path
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg failed to reformat {video_path}: {result.stderr}")

    return output_path


def cleanup_converted_video(converted_path, original_path, verbose=True):
    """
    Delete a converted video file if it's different from the original.

    This should be called after processing is complete to free disk space.

    Args:
        converted_path: Path that was returned by ensure_video_readable
        original_path: Original video path
        verbose: Print status messages
    """
    if converted_path != original_path and os.path.exists(converted_path):
        try:
            os.remove(converted_path)
            if verbose:
                print(f"      Cleaned up converted file: {os.path.basename(converted_path)}")

            # Also try to remove the converted directory if empty
            converted_dir = os.path.dirname(converted_path)
            if os.path.isdir(converted_dir) and not os.listdir(converted_dir):
                os.rmdir(converted_dir)
                if verbose:
                    print(f"      Removed empty converted directory")
        except Exception as e:
            if verbose:
                print(f"      Warning: Could not cleanup converted file: {e}")


def ensure_video_readable(video_path, verbose=True, status=None):
    """
    Ensure a video is readable by OpenCV, reformatting if necessary.

    This is the main entry point for video validation. It tests if the video
    can be read, and if not, automatically reformats it.

    Args:
        video_path: Path to video file
        verbose: Print status messages

        status: optional dict. Set status['fell_back_to_original'] = True when the video
            failed the read test and could not be repaired (the ORIGINAL path is returned and
            detection may stop early).

    Returns:
        str: Path to readable video (original or reformatted)

    Note:
        After processing, call cleanup_converted_video() to delete the
        converted file and free disk space.
    """
    is_readable, frames_read, total_frames = validate_video_readable(video_path)

    if is_readable:
        return video_path

    if verbose:
        print(f"  Video read test failed: {os.path.basename(video_path)}")
        print(f"      Only {frames_read}/{min(100, total_frames)} test frames readable")
        print(f"      Reformatting to strip problematic metadata streams...")

    try:
        reformatted_path = reformat_video_for_opencv(video_path)

        # Verify the reformatted video is readable
        is_readable, frames_read, _ = validate_video_readable(reformatted_path)

        if is_readable:
            if verbose:
                print(f"      Reformatted successfully: {reformatted_path}")
            return reformatted_path
        else:
            print(f"      WARNING: reformatted copy is still unreadable; processing the ORIGINAL file, "
                  f"detection may stop early. The video may be corrupt or truncated: {os.path.basename(video_path)}")
            if status is not None:
                status['fell_back_to_original'] = True
            return video_path  # Return original, let downstream handle the error

    except Exception as e:
        print(f"      WARNING: reformatting error ({e}); processing the ORIGINAL file, "
              f"detection may stop early: {os.path.basename(video_path)}")
        if status is not None:
            status['fell_back_to_original'] = True
        return video_path


def stride_iterator(video_path, vid_stride, stats=None):
    """
    Iterates with cv2 each vid_stride frame.

    stats: optional dict filled while iterating, so the caller can tell a complete read from one
    that OpenCV abandoned part-way: frames_expected (container frame count), frames_grabbed
    (frames OpenCV actually decoded), ended_on_failed_read (a frame could not be decoded).
    Iteration behaviour is unchanged by passing stats.
    """
    vidcap = cv2.VideoCapture(video_path)
    if stats is not None:
        stats.update(frames_expected=int(vidcap.get(cv2.CAP_PROP_FRAME_COUNT)), frames_grabbed=0,
                     ended_on_failed_read=False)
    ret, frame = vidcap.read()
    n = 0

    while vidcap.isOpened():
        n += 1
        grabbed = vidcap.grab()
        if stats is not None and grabbed:
            stats['frames_grabbed'] = n + 1  # +1 for the frame consumed by the first read()
        if n % vid_stride == 0:
            ret, frame = vidcap.retrieve()
            if ret:
                yield frame, vidcap.get(cv2.CAP_PROP_POS_MSEC), vidcap.get(cv2.CAP_PROP_POS_FRAMES)
            else:
                if stats is not None:
                    stats['ended_on_failed_read'] = True
                break


def read_completeness(stats, min_fraction=0.98):
    """Summarise stride_iterator stats: (fraction_read, truncated: bool). NaN/False if unknown."""
    expected = (stats or {}).get('frames_expected') or 0
    if expected <= 0:
        return float('nan'), False
    fraction = min(1.0, stats.get('frames_grabbed', 0) / expected)
    return fraction, fraction < min_fraction


def keyframe_iterator(video_path):
    """
    Iterates quickier with pyav each keyframe
    """
    content = av.datasets.curated(video_path)
    with av.open(content) as container:
      video_stream = container.streams.video[0]         # take only video stream
      video_stream.codec_context.skip_frame = 'NONKEY'  # and only keyframes (1fps)
      frame_idx = 0
      for frame in container.decode(video_stream):
        time_ms = round((frame.pts * video_stream.time_base) * 1000)
        yield frame.to_image(), time_ms, frame_idx
        frame_idx += 1
