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
            b / 'BRUV_station_level_MaxN.csv',
            # 2026-10-14: the study file now includes Tristan's re-run of his 17 original chapters
            b / 'TG_ORIGINALS_RERUN_20261013' / 'tracks_all.csv',
            b / 'TG_ORIGINALS_RERUN_20261013' / 'validation' / 'validation_results_TG_notes_applied_2026-10-14.csv']
    missing = [str(p) for p in need if not p.exists()]
    if missing:
        pytest.skip('private study inputs not present: ' + missing[0])
    out = tmp_path / 'out.csv'
    run(['--maxn-csv', need[0], '--durations-csv', need[1],
         '--detections', need[2], need[3], need[7], '--collections', 'BRUVs_March_Dec_2025', 'unused', 'unused',
         '--validations', need[4], need[5], need[8], '-o', out,
         # the published file predates the completeness gate and was built with unreviewed tracks
         '--allow-unreviewed', '--allow-unaccounted'])
    got = pd.read_csv(out)
    ref = pd.read_csv(need[6])
    mcols = [c for c in ref.columns if c.startswith('maxn_')]
    assert sorted(c for c in got.columns if c.startswith('maxn_')) == sorted(mcols)
    pd.testing.assert_frame_equal(got[['collection', 'station_number'] + mcols + ['n_tracks_in_window']]
                                  .reset_index(drop=True),
                                  ref[['collection', 'station_number'] + mcols + ['n_tracks_in_window']]
                                  .reset_index(drop=True))


# ---------------- completeness gate ----------------
def _gate_inputs(tmp_path, judged=(True, None), times=(0.0, 1.0)):
    """Station 1 (V1) has tracks 1 and 2; track 2's review is `judged[1]` (None = never reviewed)."""
    _final().to_csv(tmp_path / 'final.csv', index=False)
    pd.DataFrame([dict(collection='C', station_number=s, station_deploy_sec=0, station_retrieve_sec=60,
                       total_bruv_duration_sec=600, n_chapters=1) for s in (1, 2)]).to_csv(tmp_path / 'dur.csv', index=False)
    pd.DataFrame(dict(collection='C', video_id='V1', track_id=[1, 2], frame=[1, 2], time=list(times),
                      bruv_station='BRUV 001')).to_csv(tmp_path / 'd.csv', index=False)
    v = pd.DataFrame(dict(video_id='V1', track_id=[1, 2], true_detection=list(judged),
                          species=['Carcharhinus perezi', 'Carcharhinus perezi'], taxon_group='shark'))
    v.to_csv(tmp_path / 'v.csv', index=False)
    return ['--maxn-csv', tmp_path / 'final.csv', '--durations-csv', tmp_path / 'dur.csv',
            '--detections', tmp_path / 'd.csv', '--validations', tmp_path / 'v.csv', '-o', tmp_path / 'out.csv']


def run_rc(args):
    return subprocess.run([sys.executable, str(SCRIPT), *map(str, args)], capture_output=True, text=True)


def _summary(tmp_path):
    import json
    return json.load(open(tmp_path / 'out.csv.completeness.json'))


def test_gate_stops_on_unreviewed_track_in_window(tmp_path):
    r = run_rc(_gate_inputs(tmp_path))
    assert r.returncode != 0 and 'unreviewed_in_window' in r.stderr
    assert not (tmp_path / 'out.csv').exists()
    assert _summary(tmp_path)['status'] == 'FAIL' and _summary(tmp_path)['unreviewed_tracks_in_window'] == 1


def test_gate_allow_unreviewed_builds_and_counts(tmp_path):
    run(_gate_inputs(tmp_path) + ['--allow-unreviewed'])
    out = pd.read_csv(tmp_path / 'out.csv').set_index('station_number')
    assert out.loc[1, 'n_unreviewed_in_window'] == 1 and out.loc[2, 'n_unreviewed_in_window'] == 0


def test_gate_false_review_counts_as_reviewed(tmp_path):
    run(_gate_inputs(tmp_path, judged=(True, False)))
    assert _summary(tmp_path)['status'] == 'OK'


def test_gate_ignores_unreviewed_outside_window(tmp_path):
    run(_gate_inputs(tmp_path, times=(0.0, 590.0)) + ['--window-minutes', '1'])
    assert _summary(tmp_path)['status'] == 'OK'


def test_gate_deployments_must_be_analysed_or_excluded(tmp_path):
    args = _gate_inputs(tmp_path, judged=(True, False))
    pd.DataFrame(dict(station_number=[1, 2, 3], excluded_reason=['', '', ''])).to_csv(tmp_path / 'dep.csv', index=False)
    r = run_rc(args + ['--deployments', tmp_path / 'dep.csv'])
    assert r.returncode != 0 and _summary(tmp_path)['problems']['deployments_unaccounted'] == ['3']
    pd.DataFrame(dict(station_number=[1, 2, 3], excluded_reason=['', '', 'bad angle'])).to_csv(tmp_path / 'dep.csv', index=False)
    run(args + ['--deployments', tmp_path / 'dep.csv'])
    assert _summary(tmp_path)['status'] == 'OK'


def test_gate_durations_station_without_chapters_stops(tmp_path):
    args = _gate_inputs(tmp_path, judged=(True, False))
    d = pd.read_csv(tmp_path / 'dur.csv')
    pd.concat([d, d.iloc[[0]].assign(station_number=9)]).to_csv(tmp_path / 'dur.csv', index=False)
    r = run_rc(args)
    assert r.returncode != 0 and _summary(tmp_path)['problems']['durations_station_without_chapters'] == ['C 9']


def test_gate_truncated_video_stops(tmp_path):
    args = _gate_inputs(tmp_path, judged=(True, False))
    pd.DataFrame(dict(video_path=['/x/V1.MP4', '/x/V2.MP4'], tracks_found=[2, 0], truncated=[True, False],
                      read_fraction=[0.41, 1.0])).to_csv(tmp_path / 'ov.csv', index=False)
    r = run_rc(args + ['--overview', tmp_path / 'ov.csv'])
    assert r.returncode != 0 and _summary(tmp_path)['problems']['truncated_videos'][0].startswith('V1')
    run(args + ['--overview', tmp_path / 'ov.csv', '--allow-truncated'])
    assert (tmp_path / 'out.csv').exists()


def test_gate_video_missing_from_overview_stops(tmp_path):
    """A crashed video writes no overview row; V2 (station 2) is analysed but absent."""
    args = _gate_inputs(tmp_path, judged=(True, False))
    pd.DataFrame(dict(video_path=['/x/V1.MP4'], tracks_found=[2], truncated=[False], read_fraction=[1.0])
                 ).to_csv(tmp_path / 'ov.csv', index=False)
    r = run_rc(args + ['--overview', tmp_path / 'ov.csv'])
    assert r.returncode != 0 and _summary(tmp_path)['problems']['videos_missing_from_overview'] == ['V2']


# ---------------- holes found by the 2026-10-15 completeness audit ----------------
def test_gate_detections_without_final_row_stop(tmp_path):
    """Tracks of a video absent from the FINAL table were dropped before the gate; they must be reported and stop."""
    args = _gate_inputs(tmp_path, judged=(True, False))
    d = pd.read_csv(tmp_path / 'd.csv')
    extra = pd.DataFrame(dict(collection='C', video_id='V9', track_id=[1, 2, 2], frame=[1, 1, 2], time=0.0,
                              bruv_station='BRUV 001'))
    pd.concat([d, extra]).to_csv(tmp_path / 'd.csv', index=False)
    r = run_rc(args)
    assert r.returncode != 0 and 'detections_without_final_row' in r.stderr
    assert not (tmp_path / 'out.csv').exists()
    rec = _summary(tmp_path)['problems']['detections_without_final_row']
    assert len(rec) == 1
    assert rec[0]['collection'] == 'C' and rec[0]['video_id'] == 'V9' and rec[0]['station'] == 1
    assert rec[0]['n_tracks'] == 2 and rec[0]['n_unreviewed'] == 2
    r = run_rc(args + ['--allow-unmatched-videos'])
    assert r.returncode == 0 and (tmp_path / 'out.csv').exists()
    s = _summary(tmp_path)
    assert s['status'] == 'OK' and 'allow_unmatched_videos' in s['overrides']
    assert s['problems']['detections_without_final_row'][0]['n_tracks'] == 2


def test_gate_empty_overview_is_unread_not_a_crash(tmp_path):
    args = _gate_inputs(tmp_path, judged=(True, False))
    (tmp_path / 'ov.csv').write_text('')
    r = run_rc(args + ['--overview', tmp_path / 'ov.csv'])
    assert 'EmptyDataError' not in r.stderr and 'Traceback' not in r.stderr
    assert r.returncode != 0
    p = _summary(tmp_path)['problems']
    assert any('empty overview' in t for t in p['truncated_videos'])
    assert p['videos_missing_from_overview'] == ['V1', 'V2']
    r = run_rc(args + ['--overview', tmp_path / 'ov.csv', '--allow-truncated'])
    assert r.returncode == 0


def _two_collection_inputs(tmp_path):
    """V1 exists in collection C (station 1) and collection D (station 3)."""
    f = pd.concat([_final('C'), _final('D').iloc[[0]].assign(station_number=3, bruv_station='BRUV 003')])
    f.to_csv(tmp_path / 'final.csv', index=False)
    pd.DataFrame([dict(collection=c, station_number=s, station_deploy_sec=0, station_retrieve_sec=60,
                       total_bruv_duration_sec=600, n_chapters=1) for c, s in (('C', 1), ('C', 2), ('D', 3))]
                 ).to_csv(tmp_path / 'dur.csv', index=False)
    pd.DataFrame(dict(collection=['C', 'D'], video_id='V1', track_id=1, frame=1, time=0.0,
                      bruv_station=['BRUV 001', 'BRUV 003'])).to_csv(tmp_path / 'd.csv', index=False)
    pd.DataFrame(dict(video_id=['V1'], track_id=[1], true_detection=[False])).to_csv(tmp_path / 'v.csv', index=False)
    return ['--maxn-csv', tmp_path / 'final.csv', '--durations-csv', tmp_path / 'dur.csv',
            '--detections', tmp_path / 'd.csv', '--validations', tmp_path / 'v.csv', '-o', tmp_path / 'out.csv']


def test_gate_overview_matched_on_collection_and_video(tmp_path):
    args = _two_collection_inputs(tmp_path)
    # V1 finished in collection C only; V2 (C) also finished; D's V1 never did
    pd.DataFrame(dict(collection=['C', 'C'], video_path=['/x/V1.MP4', '/x/V2.MP4'], tracks_found=[1, 0],
                      truncated=False, read_fraction=1.0)).to_csv(tmp_path / 'ov.csv', index=False)
    r = run_rc(args + ['--overview', tmp_path / 'ov.csv'])
    assert r.returncode != 0
    assert _summary(tmp_path)['problems']['videos_missing_from_overview'] == ['D V1']


def test_gate_overview_collection_from_option(tmp_path):
    args = _two_collection_inputs(tmp_path)
    pd.DataFrame(dict(video_path=['/x/V1.MP4', '/x/V2.MP4'], tracks_found=[1, 0], truncated=False,
                      read_fraction=1.0)).to_csv(tmp_path / 'ov.csv', index=False)
    r = run_rc(args + ['--overview', tmp_path / 'ov.csv', '--overview-collections', 'C'])
    assert r.returncode != 0
    assert _summary(tmp_path)['problems']['videos_missing_from_overview'] == ['D V1']


def test_gate_overview_without_collection_warns_ambiguous(tmp_path):
    args = _two_collection_inputs(tmp_path)
    pd.DataFrame(dict(video_path=['/x/V1.MP4', '/x/V2.MP4'], tracks_found=[1, 0], truncated=False,
                      read_fraction=1.0)).to_csv(tmp_path / 'ov.csv', index=False)
    r = run_rc(args + ['--overview', tmp_path / 'ov.csv'])
    # backwards compatible: matches on video_id alone, so it passes, but says the check is ambiguous
    assert r.returncode == 0
    assert 'ambiguous' in r.stdout.lower() and 'V1' in r.stdout
    assert _summary(tmp_path)['problems']['overview_ambiguous_repeated_ids'] == ['V1']
