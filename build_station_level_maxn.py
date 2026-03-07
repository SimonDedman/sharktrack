#!/usr/bin/env python3
"""Build BRUV station-level MaxN CSV from detection and validation data."""

import argparse
import pandas as pd
import re
import numpy as np


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
    parser.add_argument('--window-minutes', type=float, default=60, help='Analysis window in minutes from stable start (default: 60)')
    args = parser.parse_args()

    window_sec = args.window_minutes * 60

    final = pd.read_csv(args.maxn_csv)
    sdf = pd.read_csv(args.durations_csv)

    validations = [pd.read_csv(v) for v in args.validations]

    track_species = {}
    track_taxon = {}
    true_tracks_per_det = []
    for v in validations:
        td = v[v['true_detection'] == True]
        for _, r in td.iterrows():
            tid = r['track_id']
            sp = r.get('species', np.nan)
            tg = r.get('taxon_group', np.nan)
            track_species[tid] = sp if pd.notna(sp) else 'Unknown'
            track_taxon[tid] = tg if pd.notna(tg) else 'unknown'
        true_tracks_per_det.append(set(td['track_id']))

    v2s, v2o = {}, {}
    for _, r in final.iterrows():
        v2s[(r['collection'], r['video_id'])] = r['station_number']
        v2o[(r['collection'], r['video_id'])] = float(r['chapter_offset_sec'])

    all_dets = []
    for i, det_path in enumerate(args.detections):
        det = pd.read_csv(det_path)
        true_tracks = true_tracks_per_det[i] if i < len(true_tracks_per_det) else set()

        is_2025_format = 'video_name' in det.columns and 'video_id' not in det.columns

        if is_2025_format:
            det['video_id'] = det['video_name'].str.replace('.MP4', '', case=False)
            if 'collection' not in det.columns:
                collections = final['collection'].unique()
                det['collection'] = collections[0] if len(collections) == 1 else 'unknown'

        valid_vids = set()
        for c in det['collection'].unique():
            valid_vids.update(final[final['collection'] == c]['video_id'])
        det = det[det['video_id'].isin(valid_vids)].copy()

        if 'bruv_station' in det.columns:
            det['station_number'] = det['bruv_station'].str.extract(r'(\d+)').astype(float)
        else:
            det['station_number'] = det.apply(
                lambda r: v2s.get((r['collection'], r['video_id']), np.nan), axis=1)

        det['co'] = det.apply(lambda r: v2o.get((r['collection'], r['video_id']), 0), axis=1)
        det['ts'] = det['time'].apply(parse_time)
        det['bt'] = det['co'] + det['ts']

        d = det[det['track_id'].isin(true_tracks)].copy()
        d['species'] = d['track_id'].map(track_species).fillna('Unknown')
        d['taxon_group'] = d['track_id'].map(track_taxon).fillna('unknown')

        if is_2025_format:
            d['btk'] = d['track_id'].astype(str)
        else:
            d['btk'] = d['collection'].astype(str) + '|' + d['track_id'].astype(str)

        all_dets.append(d[['collection', 'station_number', 'video_id', 'frame', 'bt', 'btk', 'species', 'taxon_group']])

    alldet = pd.concat(all_dets, ignore_index=True)
    print(f'Total true detections: {len(alldet)} rows, {alldet["btk"].nunique()} tracks')

    rows = []
    for _, srow in sdf.iterrows():
        c = srow['collection']
        s = int(srow['station_number'])
        st = srow['station_deploy_sec']
        dur = srow['station_stable_sec']
        td = srow['total_bruv_duration_sec']
        sm = dur / 60

        window_start = st
        window_end = min(st + window_sec, td)
        analysis_window_min = (window_end - window_start) / 60

        g = alldet[(alldet['collection'] == c) & (alldet['station_number'] == s)]
        gw = g[(g['bt'] >= window_start) & (g['bt'] <= window_end)]

        frows = final[(final['collection'] == c) & (final['station_number'] == s)]
        if len(frows) == 0:
            continue
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
            'retrieve_sec': srow['station_retrieve_sec'],
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
        row['gopro_total_duration_sec'] = frows['gopro_duration_sec'].sum()
        row['gopro_total_duration_min'] = frows['gopro_duration_min'].sum()
        row['gopro_total_file_size_mb'] = frows['gopro_file_size_mb'].sum()
        row['gopro_water_clarity'] = frows['gopro_water_clarity'].mean()
        row['gopro_light_level'] = frows['gopro_light_level'].mean()
        row['gopro_substrate_auto'] = meta.get('gopro_substrate_auto', '')
        row['gopro_substrate_confidence'] = frows['gopro_substrate_confidence'].mean()

        tg_maxn = maxn_by_taxon(gw)
        for tg in ['shark', 'ray_skate', 'teleost', 'invertebrate', 'turtle', 'other']:
            row[f'maxn_{tg}'] = tg_maxn.get(tg, 0)

        sp_maxn = maxn_by_species(gw)
        for sp, mx in sorted(sp_maxn.items()):
            col = f'maxn_{sp.replace(" ", "_")}'
            row[col] = mx

        row['n_tracks_in_window'] = gw['btk'].nunique()
        rows.append(row)

    result = pd.DataFrame(rows)
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
