#!/usr/bin/env python3
"""Build the station timeline for multi-chapter GoPro BRUV deployments.

A GoPro splits one recording into ~4 GB chapter files. For station-level MaxN every
detection time has to be placed on one station clock, which needs the length of every
chapter before it. This tool walks a collection folder (one sub-folder per station),
orders the chapters, reads their durations with ffprobe, and writes the two tables that
``build_station_level_maxn.py`` consumes:

  chapters.csv                per chapter: collection, station, video_id, chapter_number,
                              chapter_offset_sec, chapter_duration_sec, status, metadata
  station_level_durations.csv per station: n_chapters, total_bruv_duration_sec,
                              station_deploy_sec, station_retrieve_sec
  timeline_problems.csv       everything that is wrong, one row per problem

Chapter naming (GoPro):
  GHccnnnn.MP4 / GXccnnnn.MP4   cc = chapter (01, 02, ...), nnnn = file (recording) number
  GOPRnnnn.MP4, GPccnnnn.MP4    older cameras: GOPR = chapter 1, GP01 = chapter 2, ...

Failure policy: a station is only written to station_level_durations.csv when every
chapter 1..N exists and every chapter is readable by ffprobe. A chapter that ffprobe cannot
open (for example "moov atom not found" on a truncated copy), a gap in the chapter
numbers, more than one recording in a folder, or a missing settle time puts the station
in an explicit error state: it is listed in timeline_problems.csv, shown in a banner at the
end of the run, left OUT of station_level_durations.csv, and the exit status is 2.
It is never silently skipped. A non-final chapter much shorter than its siblings is
reported as a WARNING (possible truncation) and does not exclude the station.

Settle times (deploy = lead-in before the camera is stable, retrieve = tail before the
camera is lifted) come from ``--settle-csv``: either the per-file CSV written by
``validate_deployment.py apply`` / ``generate`` or a station-level CSV with
station_number, station_deploy_sec, station_retrieve_sec. Deploy is taken from the first
chapter and retrieve from the last.

Example:
  python utils/station_timeline.py \\
      --collection Summer_2022_46_62="/media/ssd/BRUV_Summer_2022_46_62" \\
      --settle-csv stable_durations.csv --metadata meta_data.csv -o timeline/
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

CHAPTER_RE = re.compile(r'^G[HX](\d{2})(\d{4})$', re.IGNORECASE)
LEGACY_FIRST_RE = re.compile(r'^GOPR(\d{4})$', re.IGNORECASE)
LEGACY_NEXT_RE = re.compile(r'^GP(\d{2})(\d{4})$', re.IGNORECASE)

STATION_COLS = ['collection', 'station_number', 'station_deploy_sec', 'station_retrieve_sec',
                'total_bruv_duration_sec', 'n_chapters', 'settle_source', 'missing_chapters']
SHORT_CHAPTER_FRACTION = 0.9  # non-final chapter below this x the longest sibling: warn


def parse_chapter_name(stem):
    """Return (chapter_number, file_number) from a GoPro file stem, or None."""
    m = CHAPTER_RE.match(stem)
    if m:
        return int(m.group(1)), m.group(2)
    m = LEGACY_FIRST_RE.match(stem)
    if m:
        return 1, m.group(1)
    m = LEGACY_NEXT_RE.match(stem)
    if m:
        return int(m.group(1)) + 1, m.group(2)
    return None


def station_number_from_folder(name):
    m = re.search(r'(\d+)', name)
    return int(m.group(1)) if m else None


def probe(path, timeout=120):
    """ffprobe a file. Returns dict(ok, duration_sec, error, codec, width, height, fps)."""
    cmd = ['ffprobe', '-v', 'error', '-show_entries',
           'format=duration:stream=codec_type,codec_name,width,height,r_frame_rate',
           '-of', 'json', str(path)]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except FileNotFoundError:
        raise SystemExit('ffprobe not found on PATH (install ffmpeg)')
    except subprocess.TimeoutExpired:
        return dict(ok=False, error=f'ffprobe timed out after {timeout}s')
    if r.returncode != 0:
        return dict(ok=False, error=(r.stderr.strip().splitlines() or ['ffprobe failed'])[-1])
    try:
        info = json.loads(r.stdout or '{}')
        dur = float(info.get('format', {}).get('duration'))
    except (TypeError, ValueError):
        err = (r.stderr.strip().splitlines() or ['no duration reported'])[-1]
        return dict(ok=False, error=err)
    if not np.isfinite(dur) or dur <= 0:
        return dict(ok=False, error=f'non-positive duration {dur}')
    video = next((s for s in info.get('streams', []) if s.get('codec_type') == 'video'), {})
    fps = np.nan
    try:
        num, den = video.get('r_frame_rate', '0/1').split('/')
        fps = float(num) / float(den) if float(den) else np.nan
    except ValueError:
        pass
    return dict(ok=True, duration_sec=dur, error='', codec=video.get('codec_name', ''),
                width=video.get('width'), height=video.get('height'), fps=fps)


# ---- settle times -------------------------------------------------------------------------------

def load_settle(paths):
    """Load settle-time CSVs. Returns (per_file, per_station).

    per_file:    {(folder_name, file_stem): (deploy_sec, retrieve_tail_sec)}
    per_station: {(collection_or_None, station_number): (deploy_sec, retrieve_tail_sec)}
    retrieve is the TAIL length (seconds between retrieval and end of recording).
    """
    per_file, per_station = {}, {}
    for p in paths or []:
        df = pd.read_csv(p)
        cols = set(df.columns)
        if {'station_number', 'station_deploy_sec', 'station_retrieve_sec'} <= cols:
            for _, r in df.iterrows():
                coll = r['collection'] if 'collection' in cols else None
                per_station[(coll, int(r['station_number']))] = (
                    float(r['station_deploy_sec']), float(r['station_retrieve_sec']))
            continue
        path_col = next((c for c in ('video_path', 'video_file') if c in cols), None)
        if path_col is None:
            raise SystemExit(f'--settle-csv {p}: need video_path/video_file columns or '
                             f'station_number/station_deploy_sec/station_retrieve_sec')
        for _, r in df.iterrows():
            vp = Path(str(r[path_col]))
            total = r.get('total_duration_sec', np.nan)
            if 'deploy_final_sec' in cols:  # validate_deployment.py apply output
                deploy = r['deploy_final_sec']
                tail = (total - r['retrieve_final_sec']) if 'retrieve_final_sec' in cols else np.nan
            else:  # generate / checkpoint format: retrieve_sec already is the tail
                deploy = r.get('deploy_sec', np.nan)
                tail = r.get('retrieve_sec', np.nan)
            per_file[(vp.parent.name, vp.stem.upper())] = (float(deploy), float(tail))
    return per_file, per_station


# ---- main build ---------------------------------------------------------------------------------

def build_collection(collection, root, settle_file, settle_station, require_settle, problems,
                     allow_gaps=False):
    """Return (chapter_rows, station_rows) for one collection folder."""
    root = Path(root)
    if not root.is_dir():
        raise SystemExit(f'{root} is not a directory')
    chapter_rows, station_rows = [], []

    def problem(station, level, kind, detail, file=''):
        problems.append(dict(collection=collection, station=station, level=level,
                             kind=kind, file=file, detail=detail))

    skip_dirs = {'analysis_results', 'processed', 'thumbnails', 'output', 'outputs'}
    for sdir in sorted((d for d in root.iterdir()
                        if d.is_dir() and not d.name.startswith(('.', '@')) and d.name.lower() not in skip_dirs),
                       key=lambda d: (station_number_from_folder(d.name) or 10**9, d.name)):
        mp4s = sorted(f for f in sdir.iterdir() if f.is_file() and f.suffix.lower() == '.mp4'
                      and not f.name.startswith('._'))  # '._' = macOS resource-fork litter
        files = []
        for f in mp4s:
            parsed = parse_chapter_name(f.stem)
            if parsed is None:
                problem(sdir.name, 'WARNING', 'UNRECOGNISED_NAME',
                        'MP4 not named like a GoPro chapter; ignored', f.name)
                continue
            files.append((parsed[0], parsed[1], f))
        if not files:
            if mp4s or any(sdir.iterdir()):
                problem(sdir.name, 'WARNING', 'NO_CHAPTERS', 'folder has no GoPro chapter MP4 files')
            continue

        station_number = station_number_from_folder(sdir.name)
        station_errors = 0
        missing = []

        recordings = sorted({fn for _, fn, _ in files})
        if len(recordings) > 1:
            problem(sdir.name, 'ERROR', 'MULTIPLE_RECORDINGS',
                    f'file numbers {recordings} in one station folder; split them or pass one recording')
            station_errors += 1
        files.sort(key=lambda t: (t[1], t[0]))

        chapters = [c for c, _, _ in files]
        if len(recordings) == 1:
            expected = list(range(1, max(chapters) + 1))
            missing = sorted(set(expected) - set(chapters))
            if missing:
                if allow_gaps:
                    problem(sdir.name, 'WARNING', 'CHAPTER_GAP_ALLOWED',
                            f'chapters present {chapters}; missing {missing}. Offsets treat the '
                            f'present chapters as contiguous; the missing footage is not on the clock')
                else:
                    problem(sdir.name, 'ERROR', 'CHAPTER_GAP',
                            f'chapters present {chapters}; missing {missing}. Offsets after the gap '
                            f'would be wrong (use --allow-chapter-gaps to accept)')
                    station_errors += 1
            dupes = sorted({c for c in chapters if chapters.count(c) > 1})
            if dupes:
                problem(sdir.name, 'ERROR', 'DUPLICATE_CHAPTER', f'chapter numbers repeated: {dupes}')
                station_errors += 1

        probed = []
        for cnum, fnum, f in files:
            pr = probe(f)
            pr['size_mb'] = round(f.stat().st_size / 1e6, 2)
            if not pr['ok']:
                problem(sdir.name, 'ERROR', 'UNREADABLE_CHAPTER', pr['error'], f.name)
                station_errors += 1
            probed.append((cnum, fnum, f, pr))

        good = [pr['duration_sec'] for _, _, _, pr in probed if pr['ok']]
        longest = max(good) if good else 0
        last_chapter = max(chapters)
        for cnum, fnum, f, pr in probed:
            if pr['ok'] and cnum != last_chapter and longest and pr['duration_sec'] < SHORT_CHAPTER_FRACTION * longest:
                problem(sdir.name, 'WARNING', 'SHORT_NONFINAL_CHAPTER',
                        f'{pr["duration_sec"]:.1f}s vs longest {longest:.1f}s: possible truncation', f.name)

        # offsets: cumulative sum of preceding readable chapters; invalid when anything before is unusable
        offset = 0.0
        valid = station_errors == 0
        per_station_rows = []
        for cnum, fnum, f, pr in probed:
            per_station_rows.append(dict(
                collection=collection, station_folder=sdir.name, station_number=station_number,
                bruv_station=f'BRUV {station_number:03d}' if station_number is not None else sdir.name,
                video_id=f.stem, chapter_number=cnum, file_number=fnum,
                chapter_offset_sec=round(offset, 3) if valid else np.nan,
                chapter_duration_sec=round(pr['duration_sec'], 3) if pr['ok'] else np.nan,
                status='OK' if valid and pr['ok'] else ('UNREADABLE' if not pr['ok'] else 'STATION_ERROR'),
                path=str(f),
                gopro_duration_sec=round(pr['duration_sec'], 2) if pr['ok'] else np.nan,
                gopro_duration_min=round(pr['duration_sec'] / 60, 3) if pr['ok'] else np.nan,
                gopro_file_size_mb=pr['size_mb'],
                gopro_codec=pr.get('codec', ''),
                gopro_resolution=(f"{pr.get('width')}x{pr.get('height')}" if pr['ok'] else ''),
                gopro_fps=pr.get('fps', np.nan)))
            if pr['ok']:
                offset += pr['duration_sec']

        # settle time
        deploy = tail = np.nan
        source = ''
        first_stem = probed[0][2].stem.upper()
        last_stem = probed[-1][2].stem.upper()
        if (sdir.name, first_stem) in settle_file and (sdir.name, last_stem) in settle_file:
            deploy = settle_file[(sdir.name, first_stem)][0]
            tail = settle_file[(sdir.name, last_stem)][1]
            source = 'per-file settle CSV'
        elif (collection, station_number) in settle_station or (None, station_number) in settle_station:
            deploy, tail = settle_station.get((collection, station_number),
                                              settle_station.get((None, station_number)))
            source = 'station-level settle CSV'
        elif not require_settle:
            deploy = tail = 0.0
            source = '--no-settle-times (assumed 0)'
        if source == '' or not (np.isfinite(deploy) and np.isfinite(tail)):
            problem(sdir.name, 'ERROR', 'NO_SETTLE_TIME',
                    'no usable deploy/retrieve times for first/last chapter in --settle-csv '
                    '(run validate_deployment.py, or pass --no-settle-times to assume 0)')
            station_errors += 1
            valid = False

        for r in per_station_rows:
            r['settle_source'] = source
            if not valid and r['status'] == 'OK':
                r['status'] = 'STATION_ERROR'
        chapter_rows.extend(per_station_rows)

        if station_errors == 0 and valid:
            total = sum(good)
            if deploy + tail >= total:
                problem(sdir.name, 'ERROR', 'SETTLE_EXCEEDS_TOTAL',
                        f'deploy {deploy} + retrieve tail {tail} >= total {total:.1f}s')
                for r in per_station_rows:
                    r['status'] = 'STATION_ERROR'
                continue
            station_rows.append(dict(collection=collection, station_number=station_number,
                                     station_deploy_sec=round(float(deploy), 3),
                                     station_retrieve_sec=round(float(tail), 3),
                                     total_bruv_duration_sec=round(total, 3),
                                     n_chapters=len(probed), settle_source=source,
                                     missing_chapters=' '.join(map(str, missing)) if len(recordings) == 1 else ''))
    return chapter_rows, station_rows


def join_metadata(chapters, meta_path):
    meta = pd.read_csv(meta_path)
    keys = ['station_number']
    if 'collection' in meta.columns:
        keys = ['collection', 'station_number']
    if 'station_number' not in meta.columns:
        # derive from a bruv_station-like column
        src = next((c for c in meta.columns if c.lower() in ('bruv_station', 'station', 'bruv', 'bruv_id')), None)
        if src is None:
            raise SystemExit(f'--metadata {meta_path}: needs a station_number or bruv_station column')
        meta['station_number'] = meta[src].astype(str).str.extract(r'(\d+)')[0].astype(float)
    meta = meta.drop_duplicates(subset=keys)
    extra = [c for c in meta.columns if c not in chapters.columns or c in keys]
    chapters['station_number'] = chapters['station_number'].astype(float)
    meta['station_number'] = meta['station_number'].astype(float)
    return chapters.merge(meta[extra], on=keys, how='left')


def main(argv=None):
    ap = argparse.ArgumentParser(
        description='Build the chapter/station timeline tables used by build_station_level_maxn.py',
        epilog=__doc__.split('Example:')[-1], formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--collection', action='append', required=True, metavar='NAME=DIR',
                    help='Collection label and its folder (one sub-folder per station). Repeatable.')
    ap.add_argument('--settle-csv', action='append', default=[],
                    help='Settle-time CSV (validate_deployment.py output, or station-level). Repeatable.')
    ap.add_argument('--no-settle-times', action='store_true',
                    help='Assume deploy = retrieve = 0 where no settle time is given (otherwise an error)')
    ap.add_argument('--allow-chapter-gaps', action='store_true',
                    help='Accept stations with missing chapter numbers (warning, not error). The present '
                         'chapters are laid end to end; the missing footage is not on the clock')
    ap.add_argument('--metadata', help='Station metadata CSV joined onto chapters.csv by station_number '
                                       '(and collection if the CSV has that column)')
    ap.add_argument('-o', '--output-dir', default='station_timeline', help='Output folder (default: station_timeline)')
    args = ap.parse_args(argv)

    settle_file, settle_station = load_settle(args.settle_csv)
    if args.no_settle_times:
        print('NOTE: --no-settle-times: stations without a settle time get deploy = retrieve = 0 '
              '(window starts at the first frame). Mark: settle_source column.')
    problems, chapter_rows, station_rows = [], [], []
    for spec in args.collection:
        if '=' not in spec:
            raise SystemExit(f'--collection expects NAME=DIR, got {spec!r}')
        name, folder = spec.split('=', 1)
        c, s = build_collection(name, folder, settle_file, settle_station,
                                require_settle=not args.no_settle_times, problems=problems,
                                allow_gaps=args.allow_chapter_gaps)
        chapter_rows += c
        station_rows += s

    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    chapters = pd.DataFrame(chapter_rows)
    stations = pd.DataFrame(station_rows, columns=STATION_COLS)
    if args.metadata and len(chapters):
        chapters = join_metadata(chapters, args.metadata)
    if len(chapters):
        # video_id must be unique within a collection
        dup = chapters[chapters.duplicated(['collection', 'video_id'], keep=False)]
        for (coll, vid), _ in dup.groupby(['collection', 'video_id']):
            problems.append(dict(collection=coll, station='', level='ERROR', kind='DUPLICATE_VIDEO_ID',
                                 file=vid, detail='same file name in two station folders; (collection, video_id) '
                                                  'must be unique for MaxN joins'))
    chapters.to_csv(out / 'chapters.csv', index=False)
    stations.to_csv(out / 'station_level_durations.csv', index=False)
    pd.DataFrame(problems, columns=['collection', 'station', 'level', 'kind', 'file', 'detail']
                 ).to_csv(out / 'timeline_problems.csv', index=False)

    n_err = sum(p['level'] == 'ERROR' for p in problems)
    n_warn = len(problems) - n_err
    print(f'{len(stations)} stations written, {len(chapters)} chapters, '
          f'{n_err} errors, {n_warn} warnings -> {out}')
    if problems:
        print('\n' + '!' * 78)
        print('TIMELINE PROBLEMS (stations with ERROR are NOT in station_level_durations.csv)')
        print('!' * 78)
        for p in problems:
            print(f'  [{p["level"]}] {p["collection"]} / {p["station"]} {p["kind"]} '
                  f'{p["file"]}: {p["detail"]}')
        print('!' * 78)
    return 2 if n_err else 0


if __name__ == '__main__':
    sys.exit(main())
