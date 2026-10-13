import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'tools'))
import collate_runs as cr


def make_run(d, video, tracks):
    d.mkdir(parents=True)
    pd.DataFrame(dict(video_path='', video_name=f'{video}.MP4', frame=1, time='00h:00m:01s:000ms',
                      track_id=tracks, folder1='BRUV 7')).to_csv(d / 'output.csv', index=False)


def test_runs_keep_track_ids_but_gain_collection_and_video_id(tmp_path):
    make_run(tmp_path / 'a', 'GH010001', [0, 1])
    make_run(tmp_path / 'b', 'GH010002', [0])
    out = tmp_path / 'all.csv'
    rc = cr.main(['--run', f'A={tmp_path / "a"}', '--run', f'B={tmp_path / "b"}', '-o', str(out)])
    assert rc == 0
    df = pd.read_csv(out)
    assert set(df.collection) == {'A', 'B'}
    assert sorted(df.track_id) == [0, 0, 1]  # not renumbered
    assert df.groupby(['collection', 'video_id', 'track_id']).ngroups == 3
    assert set(df.bruv_station) == {'BRUV 7'}


def test_run_without_output_is_reported_not_skipped(tmp_path, capsys):
    make_run(tmp_path / 'a', 'GH010001', [0])
    rc = cr.main(['--run', f'A={tmp_path / "a"}', '--run', f'Missing={tmp_path / "nope"}', '-o', str(tmp_path / 'o.csv')])
    assert rc == 2
    assert 'no output.csv found' in capsys.readouterr().out
