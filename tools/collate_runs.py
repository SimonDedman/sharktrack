#!/usr/bin/env python3
"""Combine the output.csv files of several SharkTrack runs into one tracks CSV.

Runs analysed separately (one per collection, or one Model per video) each number their
tracks from 0, so a bare track_id is NOT unique across runs. This tool adds the columns
that make a track unique again and does NOT renumber anything:

  collection    the name you give each run
  video_id      file name without extension (GH018634)
  bruv_station  station folder name when it can be told (folder1 column, or the video's parent
                folder)
  source_file   the output.csv the row came from

Downstream joins (validation CSVs, build_station_level_maxn.py) must key tracks on
(video_id, track_id), or on (collection, video_id, track_id) if a video name repeats between
collections.

Example:
  python tools/collate_runs.py --run Summer_2022=outputs/summer/internal_results \\
      --run Winter_2021=outputs/winter/internal_results -o all_tracks.csv
"""
import argparse
import json
import re
import sys
from pathlib import Path

import pandas as pd


def find_output_csv(location):
    p = Path(location)
    if p.is_file():
        return p
    for cand in (p / 'output.csv', p / 'internal_results' / 'output.csv'):
        if cand.exists():
            return cand
    return None


def station_of(row):
    folder = row.get('folder1')
    if isinstance(folder, str) and folder:
        return folder
    vp = row.get('video_path')
    if isinstance(vp, str) and '/' in vp.replace('\\', '/'):
        parent = Path(vp.replace('\\', '/')).parent.name
        if re.search(r'\d', parent):
            return parent
    return ''


def collate(runs):
    frames, coverage = [], []
    for name, location in runs:
        cov = dict(run=name, location=str(location), found=False, rows=0, tracks=0, videos=0)
        csv_path = find_output_csv(location)
        if csv_path is None:
            cov['error'] = 'no output.csv found'
            coverage.append(cov)
            continue
        df = pd.read_csv(csv_path)
        cov.update(found=True, source=str(csv_path), rows=len(df))
        if df.empty or 'track_id' not in df.columns:
            cov['error'] = 'empty or no track_id column'
            coverage.append(cov)
            continue
        name_col = 'video_name' if 'video_name' in df.columns else 'video_path'
        df['collection'] = name
        df['video_id'] = df[name_col].astype(str).map(lambda v: Path(v.replace('\\', '/')).stem)
        df['bruv_station'] = df.apply(station_of, axis=1)
        df['source_file'] = str(csv_path)
        cov.update(tracks=int(df.groupby(['video_id', 'track_id']).ngroups), videos=int(df['video_id'].nunique()))
        coverage.append(cov)
        frames.append(df)
    if not frames:
        return pd.DataFrame(), coverage
    out = pd.concat(frames, ignore_index=True)
    return out, coverage


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--run', action='append', required=True, metavar='NAME=PATH',
                    help='Run name and its output folder (or output.csv). Repeatable.')
    ap.add_argument('-o', '--output', default='all_tracks.csv')
    args = ap.parse_args(argv)

    runs = []
    for spec in args.run:
        if '=' not in spec:
            raise SystemExit(f'--run expects NAME=PATH, got {spec!r}')
        runs.append(tuple(spec.split('=', 1)))

    out, coverage = collate(runs)
    missing = [c for c in coverage if not c.get('tracks')]
    if not out.empty:
        out.to_csv(args.output, index=False)
        dup = out.groupby(['collection', 'video_id']).source_file.nunique()
        for (coll, vid), n in dup[dup > 1].items():
            print(f'WARNING: {coll}/{vid} appears in {n} different output.csv files; '
                  f'track ids restart in each, key on (video_id, track_id) per file', file=sys.stderr)
    Path(args.output).with_suffix('.coverage.json').write_text(json.dumps(coverage, indent=2))
    for c in coverage:
        print(f"{c['run']}: {c['rows']} rows, {c['tracks']} tracks, {c['videos']} videos"
              + (f"  ERROR: {c['error']}" if c.get('error') else ''))
    if missing:
        print(f'{len(missing)} run(s) contributed nothing; see {Path(args.output).with_suffix(".coverage.json")}',
              file=sys.stderr)
        return 2
    print(f'Saved {len(out)} rows to {args.output}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
