"""Tests for utils/station_timeline.py using tiny synthetic ffmpeg clips."""
import shutil
import subprocess
from pathlib import Path

import pandas as pd
import pytest

from utils import station_timeline as st

pytestmark = pytest.mark.skipif(shutil.which('ffmpeg') is None or shutil.which('ffprobe') is None,
                                reason='ffmpeg/ffprobe not installed')


def make_clip(path, seconds):
    path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'lavfi', '-i',
                    f'color=c=blue:s=64x48:r=5:d={seconds}', '-pix_fmt', 'yuv420p', str(path)],
                   check=True)


def settle_csv(tmp_path, coll_dir, station, first, last):
    rows = [dict(video_path=str(coll_dir / station / f'{first}.MP4'), total_duration_sec=4,
                 deploy_sec=1.0, retrieve_sec=0.5),
            dict(video_path=str(coll_dir / station / f'{last}.MP4'), total_duration_sec=2,
                 deploy_sec=0.5, retrieve_sec=0.25)]
    p = tmp_path / 'settle.csv'
    pd.DataFrame(rows).to_csv(p, index=False)
    return p


def test_parse_chapter_name():
    assert st.parse_chapter_name('GH018634') == (1, '8634')
    assert st.parse_chapter_name('GX030130') == (3, '0130')
    assert st.parse_chapter_name('GOPR3799') == (1, '3799')
    assert st.parse_chapter_name('GP023799') == (3, '3799')
    assert st.parse_chapter_name('IMG_0001') is None


def test_offsets_are_cumulative_and_settle_applied(tmp_path):
    coll = tmp_path / 'coll'
    make_clip(coll / 'BRUV 7' / 'GH010001.MP4', 4)
    make_clip(coll / 'BRUV 7' / 'GH020001.MP4', 2)
    settle = settle_csv(tmp_path, coll, 'BRUV 7', 'GH010001', 'GH020001')
    rc = st.main(['--collection', f'C={coll}', '--settle-csv', str(settle), '-o', str(tmp_path / 'out')])
    assert rc == 0
    ch = pd.read_csv(tmp_path / 'out' / 'chapters.csv')
    assert list(ch.video_id) == ['GH010001', 'GH020001']
    assert ch.chapter_offset_sec[0] == 0
    assert abs(ch.chapter_offset_sec[1] - ch.chapter_duration_sec[0]) < 1e-6
    sd = pd.read_csv(tmp_path / 'out' / 'station_level_durations.csv')
    assert sd.n_chapters[0] == 2 and sd.station_deploy_sec[0] == 1.0 and sd.station_retrieve_sec[0] == 0.25
    assert abs(sd.total_bruv_duration_sec[0] - ch.chapter_duration_sec.sum()) < 1e-6


def test_chapter_gap_is_an_error_not_a_skip(tmp_path, capsys):
    coll = tmp_path / 'coll'
    make_clip(coll / 'BRUV 8' / 'GH010002.MP4', 2)
    make_clip(coll / 'BRUV 8' / 'GH030002.MP4', 2)
    rc = st.main(['--collection', f'C={coll}', '--no-settle-times', '-o', str(tmp_path / 'out')])
    assert rc == 2
    assert 'CHAPTER_GAP' in capsys.readouterr().out
    assert pd.read_csv(tmp_path / 'out' / 'station_level_durations.csv').empty
    probs = pd.read_csv(tmp_path / 'out' / 'timeline_problems.csv')
    assert 'CHAPTER_GAP' in set(probs.kind)
    # with the opt-in flag the station is kept but still reported
    rc = st.main(['--collection', f'C={coll}', '--no-settle-times', '--allow-chapter-gaps',
                  '-o', str(tmp_path / 'out2')])
    assert rc == 0
    sd = pd.read_csv(tmp_path / 'out2' / 'station_level_durations.csv')
    assert sd.missing_chapters[0] == 2


def test_unreadable_chapter_is_an_error_state(tmp_path, capsys):
    coll = tmp_path / 'coll'
    make_clip(coll / 'BRUV 9' / 'GH010003.MP4', 2)
    good = coll / 'BRUV 9' / 'GH020003.MP4'
    make_clip(good, 2)
    data = good.read_bytes()
    good.write_bytes(data[: len(data) // 3])  # truncated: no usable moov box
    rc = st.main(['--collection', f'C={coll}', '--no-settle-times', '-o', str(tmp_path / 'out')])
    assert rc == 2
    assert 'UNREADABLE_CHAPTER' in capsys.readouterr().out
    ch = pd.read_csv(tmp_path / 'out' / 'chapters.csv')
    assert 'UNREADABLE' in set(ch.status)
    assert pd.read_csv(tmp_path / 'out' / 'station_level_durations.csv').empty


def test_missing_settle_time_is_an_error_unless_opted_out(tmp_path):
    coll = tmp_path / 'coll'
    make_clip(coll / 'BRUV 10' / 'GH010004.MP4', 2)
    assert st.main(['--collection', f'C={coll}', '-o', str(tmp_path / 'a')]) == 2
    assert st.main(['--collection', f'C={coll}', '--no-settle-times', '-o', str(tmp_path / 'b')]) == 0
