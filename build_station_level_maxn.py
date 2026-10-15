#!/usr/bin/env python3
"""Build BRUV station-level MaxN CSV from detection and validation data.

Method (the one used for the reef-shark manuscript):
  * A track is identified by (video_id, track_id), never by track_id alone.
    When videos are analysed in separate runs, track ids restart per video and
    collide across runs, so a bare track_id conflates species and taxa between
    runs and inflates MaxN (study: shark 97 -> 76 after the fix).
  * Only tracks marked true_detection in the validation CSVs are counted.
  * MaxN = max over frames of the number of distinct tracks, per taxon group and
    per species, inside an analysis window of --window-minutes starting at the
    stable (post-settling) start of the station.
  * Station time = chapter_offset_sec (from the per-chapter table) + time in
    video. Build the per-chapter table and the durations table with
    utils/station_timeline.py.
  * Stable duration = total - deploy (lead-in) - retrieve (tail) unless the
    durations CSV already has station_stable_sec.

Completeness gate (added after the reef-shark study found 1,870 unreviewed tracks and a deployment with no
tracks had silently been left out; an unreviewed track and a missing station both look like "no animals"):
  * Every track inside an analysed window must have been reviewed (true_detection true or false). Unreviewed
    tracks stop the build; --allow-unreviewed builds anyway and the per-station count is written to
    n_unreviewed_in_window.
  * Every station in the durations CSV must have rows in the per-chapter table (it used to be skipped).
  * --deployments CSV (station_number, optional collection and excluded_reason): every deployment must be
    analysed or carry an excluded_reason. Videos with no tracks write no detection rows, so without this list
    a zero-track deployment cannot be told apart from one that was never run.
  * --overview CSV(s) (SharkTrack overview.csv): a video of an analysed station that is flagged truncated, read
    below 99%, or absent from every overview (it crashed or was never run) stops the build (--allow-truncated).
  A summary <output>.completeness.json is written on every run, pass or fail.
"""

import argparse
import json
import os
import pandas as pd
import re
import numpy as np


def key(vid, tid):
    """Track key: (video_id, track_id) as a single string; ids may be float-typed."""
    try:
        return f'{vid}|{int(float(tid))}'
    except Exception:
        return f'{vid}|{tid}'


def col_agg(df, col, how):
    """Aggregate an optional column; NaN when the per-chapter table does not have it."""
    if col not in df.columns:
        return np.nan
    return getattr(df[col], how)()


def parse_time(t):
    m = re.match(r'(\d+)h:(\d+)m:(\d+)s:(\d+)ms', str(t))
    if m:
        return int(m[1]) * 3600 + int(m[2]) * 60 + int(m[3]) + int(m[4]) / 1000
    try:
        return float(t)
    except Exception:
        return np.nan


def maxn_by_species(df):
    result = {}
    for sp, gsp in df.groupby('species'):
        if len(gsp) == 0:
            continue
        maxn = int(gsp.groupby(['video_id', 'frame'])['btk'].nunique().max())
        result[sp] = maxn
    return result


def maxn_by_taxon(df):
    result = {}
    for tg, gtg in df.groupby('taxon_group'):
        if len(gtg) == 0:
            continue
        maxn = int(gtg.groupby(['video_id', 'frame'])['btk'].nunique().max())
        result[tg] = maxn
    return result


def main():
    parser = argparse.ArgumentParser(
        description='Build BRUV station-level MaxN CSV from detection and validation data.',
        epilog='''examples:
  %(prog)s \\
    --maxn-csv FINAL_MaxN_all_BRUVs.csv \\
    --durations-csv station_level_durations.csv \\
    --detections output_bruv2025.csv reanalysis_all_tracks.csv \\
    --validations validation_results_bruv2025.csv validation_results_TG.csv \\
    -o station_level_maxn.csv

  %(prog)s \\
    --maxn-csv FINAL_MaxN.csv \\
    --durations-csv durations.csv \\
    --detections detections.csv \\
    --validations validations.csv \\
    --window-minutes 90
''',
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument('--maxn-csv', required=True, help='Per-chapter MaxN CSV (FINAL_MaxN_all_BRUVs.csv format)')
    parser.add_argument('--durations-csv', required=True, help='Station-level durations CSV')
    parser.add_argument('--detections', required=True, nargs='+', help='One or more detection CSV paths (raw frame-level)')
    parser.add_argument('--validations', required=True, nargs='+', help='One or more validation CSV paths')
    parser.add_argument('-o', '--output', default='station_level_maxn.csv', help='Output path (default: station_level_maxn.csv)')
    parser.add_argument('--collections', nargs='+', default=None,
                        help='Collection name for each --detections file that has no collection column '
                             '(same order as --detections)')
    parser.add_argument('--window-minutes', type=float, default=60, help='Analysis window in minutes from stable start (default: 60)')
    parser.add_argument('--deployments', help='CSV listing every deployment (station_number; optional collection, '
                                              'excluded_reason). Each must be analysed or carry an excluded_reason.')
    parser.add_argument('--overview', nargs='+', default=[], help="SharkTrack overview.csv file(s); truncated videos stop the build")
    parser.add_argument('--allow-unreviewed', action='store_true',
                        help='Build even if tracks inside analysed windows have no review (counted per station)')
    parser.add_argument('--allow-truncated', action='store_true', help='Build even if a video was not read in full or has no overview row')
    parser.add_argument('--allow-unaccounted', action='store_true',
                        help='Build even if a deployment or a durations station is missing from the analysis')
    args = parser.parse_args()

    window_sec = args.window_minutes * 60

    final = pd.read_csv(args.maxn_csv)
    sdf = pd.read_csv(args.durations_csv)

    validations = [pd.read_csv(v) for v in args.validations]

    # (video_id, track_id) -> species / taxon, from confirmed true detections
    track_species, track_taxon = {}, {}
    true_keys_per_det, reviewed_keys_per_det = [], []
    for vpath, v in zip(args.validations, validations):
        for col in ('video_id', 'track_id', 'true_detection'):
            if col not in v.columns:
                raise SystemExit(f'Validation file {vpath} lacks required column {col!r}')
        judged = v['true_detection'].map(lambda x: str(x).strip().lower() in ('true', 'false', '1', '0', '1.0', '0.0'))
        reviewed_keys_per_det.append({key(a, b) for a, b in zip(v.loc[judged, 'video_id'], v.loc[judged, 'track_id'])})
        td = v[v['true_detection'].map(lambda x: str(x).strip().lower() in ('true', '1', '1.0'))]
        keys = set()
        for _, r in td.iterrows():
            k = key(r['video_id'], r['track_id'])
            sp = r.get('species', np.nan)
            tg = r.get('taxon_group', np.nan)
            track_species[k] = sp if pd.notna(sp) else 'Unknown'
            track_taxon[k] = tg if pd.notna(tg) else 'unknown'
            keys.add(k)
        true_keys_per_det.append(keys)

    if len(args.validations) != len(args.detections):
        print(f'WARNING: {len(args.detections)} detection files but {len(args.validations)} '
              f'validation files; they are paired by position, unpaired detection files count nothing.')

    v2s, v2o = {}, {}
    for _, r in final.iterrows():
        v2s[(r['collection'], r['video_id'])] = r['station_number']
        v2o[(r['collection'], r['video_id'])] = float(r['chapter_offset_sec'])

    collections_arg = args.collections or []
    all_dets, unrev_dets = [], []
    seen_videos = {}
    for i, det_path in enumerate(args.detections):
        det = pd.read_csv(det_path)
        true_keys = true_keys_per_det[i] if i < len(true_keys_per_det) else set()
        reviewed_keys = reviewed_keys_per_det[i] if i < len(reviewed_keys_per_det) else set()

        is_2025_format = 'video_name' in det.columns and 'video_id' not in det.columns

        if is_2025_format:
            det['video_id'] = det['video_name'].str.replace('.MP4', '', case=False)
        if 'collection' not in det.columns:
            if i < len(collections_arg):
                det['collection'] = collections_arg[i]
            else:
                collections = final['collection'].unique()
                det['collection'] = collections[0] if len(collections) == 1 else 'unknown'
                if len(collections) != 1:
                    print(f'WARNING: {det_path} has no collection column and --collections was not given; '
                          f'using "unknown" (nothing will match)')

        valid_vids = set()
        for c in det['collection'].unique():
            valid_vids.update(final[final['collection'] == c]['video_id'])
        det = det[det['video_id'].isin(valid_vids)].copy()

        for cv in set(zip(det['collection'], det['video_id'])):
            if cv in seen_videos and seen_videos[cv] != i:
                print(f'WARNING: video {cv[1]} ({cv[0]}) appears in detection files '
                      f'{seen_videos[cv]} and {i}; its tracks are counted separately in each run')
            seen_videos.setdefault(cv, i)

        if 'bruv_station' in det.columns:
            det['station_number'] = det['bruv_station'].str.extract(r'(\d+)').astype(float)
        else:
            det['station_number'] = [v2s.get((c, v), np.nan)
                                     for c, v in zip(det['collection'], det['video_id'])]

        det['co'] = [v2o.get((c, v), 0) for c, v in zip(det['collection'], det['video_id'])]
        det['ts'] = det['time'].apply(parse_time)
        det['bt'] = det['co'] + det['ts']
        det['k'] = [key(v, t) for v, t in zip(det['video_id'], det['track_id'])]

        u = det[~det['k'].isin(reviewed_keys)]
        unrev_dets.append(u.assign(src=os.path.basename(det_path))[['collection', 'station_number', 'video_id', 'bt', 'k', 'src']])

        d = det[det['k'].isin(true_keys)].copy()
        d['species'] = d['k'].map(track_species).fillna('Unknown')
        d['taxon_group'] = d['k'].map(track_taxon).fillna('unknown')

        # btk: unique track id across detection files. Reanalysis-style files restart ids per
        # video, so the key includes the video; collection is prefixed for non-2025 formats.
        if is_2025_format:
            d['btk'] = d['k']
        else:
            d['btk'] = d['collection'].astype(str) + '|' + d['k']

        all_dets.append(d[['collection', 'station_number', 'video_id', 'frame', 'bt', 'btk', 'species', 'taxon_group']])

    alldet = pd.concat(all_dets, ignore_index=True)
    print(f'Total true detections: {len(alldet)} rows, {alldet["btk"].nunique()} tracks')

    unrev = pd.concat(unrev_dets, ignore_index=True)
    problems = {'unreviewed_in_window': {}, 'durations_station_without_chapters': [], 'deployments_unaccounted': [],
                'truncated_videos': [], 'videos_missing_from_overview': []}
    rows = []
    for _, srow in sdf.iterrows():
        c = srow['collection']
        s = int(srow['station_number'])
        st = srow['station_deploy_sec']
        retrieve = srow['station_retrieve_sec']
        td = srow['total_bruv_duration_sec']
        if 'station_stable_sec' in srow.index and pd.notna(srow['station_stable_sec']):
            dur = srow['station_stable_sec']
        else:
            dur = td - st - retrieve  # stable = total - lead-in - tail
        sm = dur / 60

        window_start = st
        window_end = min(st + window_sec, td)
        analysis_window_min = (window_end - window_start) / 60

        g = alldet[(alldet['collection'] == c) & (alldet['station_number'] == s)]
        gw = g[(g['bt'] >= window_start) & (g['bt'] <= window_end)]

        frows = final[(final['collection'] == c) & (final['station_number'] == s)]
        if len(frows) == 0:
            problems['durations_station_without_chapters'].append(f'{c} {s}')
            continue
        uw = unrev[(unrev['collection'] == c) & (unrev['station_number'] == s)
                   & (unrev['bt'] >= window_start) & (unrev['bt'] <= window_end)]
        n_unrev = uw[['src', 'k']].drop_duplicates().shape[0]
        if n_unrev:
            problems['unreviewed_in_window'][f'{c} {s}'] = n_unrev
        meta = frows.iloc[0]

        row = {
            'collection': c,
            'station_number': s,
            'bruv_station': meta.get('bruv_station', f'BRUV {s:03d}'),
            'lat': meta.get('lat', np.nan),
            'lon': meta.get('lon', np.nan),
            'Date': meta.get('Date', ''),
            'time_in': meta.get('time_in', ''),
            'time_out': meta.get('time_out', ''),
            'soak_time': meta.get('soak_time', ''),
            'temp_deg_C': meta.get('temp_deg_C', np.nan),
            'depth_m': meta.get('depth_m', np.nan),
            'habitat': meta.get('habitat', ''),
            'substrate': meta.get('substrate', ''),
            'tide': meta.get('tide', ''),
            'bait': meta.get('bait', ''),
            'n_chapters': int(srow['n_chapters']),
            'total_bruv_duration_sec': td,
            'total_bruv_duration_min': td / 60,
            'deploy_sec': st,
            'retrieve_sec': retrieve,
            'stable_duration_sec': dur,
            'stable_duration_min': sm,
            'analysis_window_min': analysis_window_min,
        }

        row['gopro_camera_model'] = meta.get('gopro_camera_model', '')
        row['gopro_camera_serial'] = meta.get('gopro_camera_serial', '')
        row['gopro_lens_serial'] = meta.get('gopro_lens_serial', '')
        row['gopro_resolution'] = meta.get('gopro_resolution', '')
        row['gopro_codec'] = meta.get('gopro_codec', '')
        row['gopro_fps'] = meta.get('gopro_fps', np.nan)
        row['gopro_field_of_view'] = meta.get('gopro_field_of_view', '')
        row['gopro_auto_rotation'] = meta.get('gopro_auto_rotation', '')
        row['gopro_firmware'] = meta.get('gopro_firmware', '')
        row['gopro_creation_time'] = meta.get('gopro_creation_time', '')
        row['gopro_total_duration_sec'] = col_agg(frows, 'gopro_duration_sec', 'sum')
        row['gopro_total_duration_min'] = col_agg(frows, 'gopro_duration_min', 'sum')
        row['gopro_total_file_size_mb'] = col_agg(frows, 'gopro_file_size_mb', 'sum')
        row['gopro_water_clarity'] = col_agg(frows, 'gopro_water_clarity', 'mean')
        row['gopro_light_level'] = col_agg(frows, 'gopro_light_level', 'mean')
        row['gopro_substrate_auto'] = meta.get('gopro_substrate_auto', '')
        row['gopro_substrate_confidence'] = col_agg(frows, 'gopro_substrate_confidence', 'mean')

        tg_maxn = maxn_by_taxon(gw)
        for tg in ['shark', 'ray_skate', 'teleost', 'invertebrate', 'turtle', 'other']:
            row[f'maxn_{tg}'] = tg_maxn.get(tg, 0)

        sp_maxn = maxn_by_species(gw)
        for sp, mx in sorted(sp_maxn.items()):
            col = f'maxn_{sp.replace(" ", "_")}'
            row[col] = mx

        row['n_tracks_in_window'] = gw['btk'].nunique()
        row['n_unreviewed_in_window'] = n_unrev
        rows.append(row)

    result = pd.DataFrame(rows)
    analysed = {(r['collection'], int(r['station_number'])) for r in rows}

    if args.deployments:
        dep = pd.read_csv(args.deployments)
        if 'station_number' not in dep.columns:
            raise SystemExit(f'{args.deployments} lacks required column station_number')
        for _, d in dep.iterrows():
            s = int(float(d['station_number']))
            why = d.get('excluded_reason', np.nan)
            if pd.notna(why) and str(why).strip():
                continue
            if 'collection' in dep.columns and pd.notna(d['collection']):
                ok = (d['collection'], s) in analysed
            else:
                ok = any(st == s for _, st in analysed)
            if not ok:
                problems['deployments_unaccounted'].append(str(d.get('collection', '')) + f' {s}'.strip())

    analysed_videos = set(final[[ (c, int(s)) in analysed for c, s in zip(final['collection'], final['station_number'])]]['video_id'])
    seen_in_overview = set()
    for ov in args.overview:
        o = pd.read_csv(ov)
        o['video_id'] = o['video_path'].astype(str).map(lambda p: os.path.splitext(os.path.basename(p))[0])
        trunc = o.get('truncated', pd.Series(False, index=o.index)).astype(str).str.lower().isin(['true', '1'])
        frac = pd.to_numeric(o.get('read_fraction', pd.Series(np.nan, index=o.index)), errors='coerce')
        bad = o[(trunc | (frac < 0.99)) & o['video_id'].isin(analysed_videos)]
        problems['truncated_videos'] += [f'{v} ({ov})' for v in bad['video_id']]
        seen_in_overview.update(o['video_id'])
    if args.overview:
        # SharkTrack writes an overview row only when a video finishes, so a crashed video has none
        problems['videos_missing_from_overview'] = sorted(analysed_videos - seen_in_overview)

    blocking = []
    if problems['unreviewed_in_window'] and not args.allow_unreviewed:
        blocking.append('unreviewed_in_window')
    for k in ('truncated_videos', 'videos_missing_from_overview'):
        if problems[k] and not args.allow_truncated:
            blocking.append(k)
    for k in ('durations_station_without_chapters', 'deployments_unaccounted'):
        if problems[k] and not args.allow_unaccounted:
            blocking.append(k)
    summary = dict(stations_analysed=len(analysed), deployments_checked=bool(args.deployments),
                   overviews_checked=len(args.overview),
                   unreviewed_tracks_in_window=int(sum(problems['unreviewed_in_window'].values())),
                   problems=problems, blocking=blocking,
                   overrides=[f for f in ('allow_unreviewed', 'allow_truncated', 'allow_unaccounted') if getattr(args, f)],
                   status='FAIL' if blocking else 'OK')
    with open(args.output + '.completeness.json', 'w') as f:
        json.dump(summary, f, indent=1)
    print(f"\nCompleteness: {summary['status']}  ({len(analysed)} stations; "
          f"{summary['unreviewed_tracks_in_window']} unreviewed tracks in windows; "
          f"{len(problems['durations_station_without_chapters'])} durations stations without chapters; "
          f"{len(problems['deployments_unaccounted'])} deployments unaccounted"
          f"{'' if args.deployments else ' (NOT CHECKED: no --deployments)'}; "
          f"{len(problems['truncated_videos'])} truncated and {len(problems['videos_missing_from_overview'])} unfinished videos"
          f"{'' if args.overview else ' (NOT CHECKED: no --overview)'})")
    for k in problems:
        if problems[k]:
            print(f'  {k}: {problems[k]}')
    if blocking:
        raise SystemExit(f'STOPPED, nothing written: {", ".join(blocking)}. Fix the inputs, or pass the matching '
                         f'--allow-* flag to build anyway (see {args.output}.completeness.json).')
    sp_cols = [c for c in result.columns if c.startswith('maxn_')]
    result[sp_cols] = result[sp_cols].fillna(0).astype(int)

    result.to_csv(args.output, index=False)
    print(f'\nSaved: {args.output}')
    print(f'{len(result)} stations, {len(result.columns)} columns')
    print(f'\nMaxN totals:')
    for c in sp_cols:
        total = result[c].sum()
        if total > 0:
            print(f'  {c}: {total}')


if __name__ == '__main__':
    main()
