"""The GUI must send the flags the CLI needs, and the MaxN button must run the real script."""
import sys
from pathlib import Path
from unittest import mock

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
web_gui = pytest.importorskip('web_gui')


@pytest.fixture
def client():
    web_gui.app.config['TESTING'] = True
    return web_gui.app.test_client()


def started_command(client, payload):
    with mock.patch.object(web_gui, 'SharkTrackProcess') as proc:
        r = client.post('/api/analyze/start', json=payload)
        assert r.status_code == 200, r.data
        return proc.call_args[0][1]


def test_run_sends_no_chapters_by_default(client):
    cmd = started_command(client, {'input_path': '/v', 'output_path': '/o'})
    assert '--no-chapters' in cmd and '--chapters' not in cmd


def test_run_sends_chapters_metadata_and_surface_flags(client):
    cmd = started_command(client, {'input_path': '/v', 'chapters': True,
                                   'extract_metadata': True, 'filter_surface': True})
    assert '--chapters' in cmd and '--no-chapters' not in cmd
    assert '--extract_metadata' in cmd and '--filter_surface' in cmd


def test_maxn_command_runs_build_station_level_maxn(tmp_path):
    cmd, err = web_gui.build_maxn_command({
        'chapters_csv': 'c.csv', 'durations_csv': 'd.csv', 'detections': ['a.csv', 'b.csv'],
        'validations': ['va.csv', 'vb.csv'], 'window_minutes': 45, 'output': str(tmp_path / 'x' / 'm.csv')})
    assert err is None
    assert 'build_station_level_maxn.py' in cmd
    assert cmd[cmd.index('--detections') + 1:cmd.index('--detections') + 3] == ['a.csv', 'b.csv']
    assert cmd[cmd.index('--window-minutes') + 1] == '45'
    assert web_gui.build_maxn_command({'chapters_csv': 'c'})[0] is None


def test_chapters_option_never_prompts():
    # app.py needs the torch stack to import, so check the declaration itself
    src = (Path(__file__).resolve().parent.parent / 'app.py').read_text()
    line = next(l for l in src.splitlines() if '"--chapters' in l)
    assert '--chapters/--no-chapters' in line and 'prompt' not in line
