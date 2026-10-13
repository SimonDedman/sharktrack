"""Regression tests for build_station_level_maxn.py.

* test_track_ids_colliding_across_runs: synthetic, always runs. Two runs reuse track_id 1 for
  different species in different videos; MaxN must be keyed on (video_id, track_id).
* test_study_inputs_reproduce_published_maxn: reproduces the maxn_* columns of the reef-shark
  study's BRUV_station_level_MaxN.csv from the study's own inputs. Those files are private and
  large, so the test skips when they are absent (set SHARKTRACK_STUDY_BRUV_DIR to override).
"""
import os
import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest

REPO = Path(__file__).resolve().parent.parent
SCRIPT = REPO / 'build_station_level_maxn.py'
DEFAULT_BRUV_DIR = ('/media/simon/data/Documents/Si Work/PostDoc Work/Saving The Blue/Data/BRUV')


def run(args):
    return subprocess.run([sys.executable, str(SCRIPT), *map(str, args)],
                          capture_output=True, text=True, check=True)


def _final(collection='C'):
    rows = []
    for vid, st, off in [('V1', 1, 0), ('V2', 2, 0)]:
        rows.append(dict(collection=collection, video_id=vid, station_number=st,
                         chapter_offset_sec=off, bruv_station=f'BRUV {st:03d}', lat=0, lon=0,
                         gopro_duration_sec=600, gopro_duration_min=10, gopro_file_size_mb=1,
                         gopro_water_clarity=1, gopro_light_level=1, gopro_substrate_confidence=1))
    return pd.DataFrame(rows)


def test_track_ids_colliding_across_runs(tmp_path):
    _final().to_csv(tmp_path / 'final.csv', index=False)
    # No station_stable_sec column on purpose: it must be derived as total - deploy - retrieve
    pd.DataFrame([dict(collection='C', station_number=s, station_deploy_sec=0,
                       station_retrieve_sec=60, total_bruv_duration_sec=600, n_chapters=1)
                  for s in (1, 2)]).to_csv(tmp_path / 'dur.csv', index=False)
    # Run A: V1 track 1 = shark. Run B: V2 track 1 = teleost. Same bare track_id.
    det_a = pd.DataFrame(dict(collection='C', video_id='V1', track_id=1, frame=[1, 2],
                              time=[0.0, 1.0], bruv_station='BRUV 001'))
    det_b = pd.DataFrame(dict(collection='C', video_id='V2', track_id=1, frame=[1, 2],
                              time=[0.0, 1.0], bruv_station='BRUV 002'))
    det_a.to_csv(tmp_path / 'da.csv', index=False)
    det_b.to_csv(tmp_path / 'db.csv', index=False)
    pd.DataFrame(dict(video_id=['V1'], track_id=[1], true_detection=[True],
                      species=['Carcharhinus perezi'], taxon_group=['shark'])
                 ).to_csv(tmp_path / 'va.csv', index=False)
    pd.DataFrame(dict(video_id=['V2'], track_id=[1], true_detection=[True],
                      species=['Sphyraena barracuda'], taxon_group=['teleost'])
                 ).to_csv(tmp_path / 'vb.csv', index=False)
    run(['--maxn-csv', tmp_path / 'final.csv', '--durations-csv', tmp_path / 'dur.csv',
         '--detections', tmp_path / 'da.csv', tmp_path / 'db.csv',
         '--validations', tmp_path / 'va.csv', tmp_path / 'vb.csv',
         '-o', tmp_path / 'out.csv'])
    out = pd.read_csv(tmp_path / 'out.csv').set_index('station_number')
    assert out.loc[1, 'maxn_shark'] == 1 and out.loc[1, 'maxn_teleost'] == 0
    assert out.loc[2, 'maxn_teleost'] == 1 and out.loc[2, 'maxn_shark'] == 0
    assert out.loc[1, 'maxn_Carcharhinus_perezi'] == 1
    assert out.loc[2, 'maxn_Sphyraena_barracuda'] == 1
    assert 'maxn_Sphyraena_barracuda' in out.columns
    assert out.loc[1, 'stable_duration_sec'] == 540


def test_study_inputs_reproduce_published_maxn(tmp_path):
    b = Path(os.environ.get('SHARKTRACK_STUDY_BRUV_DIR', DEFAULT_BRUV_DIR))
    re_dir = b / 'REANALYSIS_QAQC_20251202'
    need = [b / 'FINAL_MaxN_all_BRUVs.csv', b / 'station_level_durations.csv',
            b / 'detections_bruv2025_framelevel.csv', re_dir / 'reanalysis_all_tracks.csv',
            b / 'validation_results_bruv2025 (4).csv',
            re_dir / 'validation' / 'validation_results_TG.csv',
            b / 'BRUV_station_level_MaxN.csv']
    missing = [str(p) for p in need if not p.exists()]
    if missing:
        pytest.skip('private study inputs not present: ' + missing[0])
    out = tmp_path / 'out.csv'
    run(['--maxn-csv', need[0], '--durations-csv', need[1],
         '--detections', need[2], need[3], '--collections', 'BRUVs_March_Dec_2025', 'unused',
         '--validations', need[4], need[5], '-o', out])
    got = pd.read_csv(out)
    ref = pd.read_csv(need[6])
    mcols = [c for c in ref.columns if c.startswith('maxn_')]
    assert [c for c in got.columns if c.startswith('maxn_')] == mcols
    pd.testing.assert_frame_equal(got[['collection', 'station_number'] + mcols + ['n_tracks_in_window']]
                                  .reset_index(drop=True),
                                  ref[['collection', 'station_number'] + mcols + ['n_tracks_in_window']]
                                  .reset_index(drop=True))
