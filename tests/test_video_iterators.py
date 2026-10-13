import shutil
import subprocess

import pytest

cv2 = pytest.importorskip('cv2')
av = pytest.importorskip('av')
from utils import video_iterators as vi


def test_read_completeness_flags_early_stop():
    assert vi.read_completeness({'frames_expected': 1000, 'frames_grabbed': 300}) == (0.3, True)
    assert vi.read_completeness({'frames_expected': 1000, 'frames_grabbed': 1000}) == (1.0, False)
    frac, trunc = vi.read_completeness({})
    assert frac != frac and trunc is False  # unknown stays unknown, not 'complete'


@pytest.mark.skipif(shutil.which('ffmpeg') is None, reason='ffmpeg not installed')
def test_stride_iterator_stats_on_complete_clip(tmp_path):
    clip = tmp_path / 'c.mp4'
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'lavfi', '-i', 'color=c=blue:s=64x48:r=10:d=3',
                    '-pix_fmt', 'yuv420p', str(clip)], check=True)
    stats = {}
    frames = list(vi.stride_iterator(str(clip), 5, stats=stats))
    assert len(frames) >= 5
    fraction, truncated = vi.read_completeness(stats)
    assert not truncated and fraction >= 0.98
    # same frames with and without stats: instrumentation does not change behaviour
    assert len(list(vi.stride_iterator(str(clip), 5))) == len(frames)


def test_ensure_video_readable_reports_fallback(tmp_path, capsys):
    bad = tmp_path / 'bad.mp4'
    bad.write_bytes(b'not a video')
    status = {}
    out = vi.ensure_video_readable(str(bad), verbose=True, status=status)
    assert out == str(bad)
    assert status.get('fell_back_to_original') is True
    assert 'WARNING' in capsys.readouterr().out
