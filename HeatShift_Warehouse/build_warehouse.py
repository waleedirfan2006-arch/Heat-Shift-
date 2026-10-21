"""HeatShift Step 2. Rebuild from the supplied, unchanged CSV snapshots.
Tested with Python 3.12 and the pinned requirements. No network, model training or cloud account.
All project choices below are Recommended; source encodings follow NOAA docs.
"""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import csv
import hashlib
import io
import json
import shutil
import sqlite3
import tempfile
import pandas as pd

ROOT = Path(__file__).resolve().parent
STATIONS = {'41780099999': 'Karachi', '41640099999': 'Lahore', '41675099999': 'Multan'}
GRIDS = {(25.0, 67.25): 'Karachi', (31.5, 74.25): 'Lahore', (30.25, 71.5): 'Multan'}
FIELDS = {
    'temperature_2m (°C)': ('temperature_c', -100, 65),
    'relative_humidity_2m (%)': ('relative_humidity_pct', 0, 100),
    'dew_point_2m (°C)': ('dew_point_c', -100, 65),
    'surface_pressure (hPa)': ('surface_pressure_hpa', 1, 1200),
    'cloud_cover (%)': ('cloud_cover_pct', 0, 100),
    'wind_speed_10m (km/h)': ('wind_speed_10m_kmh', 0, 500),
    'shortwave_radiation (W/m²)': ('shortwave_radiation_wm2', 0, 1600),
}
FEATURES = ['station_id', 'temp_c', 'temp_lag24_c', 'temp_lag48_c',
            'lag24_missing', 'lag48_missing', 'hour_pk', 'month_pk']
TARGET = 'target_temp_24h_c'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def stamp(value):
    return value.strftime('%Y-%m-%dT%H:%M:%SZ')

def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')

def save_csv(frame, path):
    frame.to_csv(path, index=False, lineterminator='\n', float_format='%.6f')

def quality_report(folder, audit, splits, coverage):
    def table(frame):
        cols = list(frame.columns)
        lines = ['| ' + ' | '.join(cols) + ' |', '| ' + ' | '.join(['---']*len(cols)) + ' |']
        lines += ['| ' + ' | '.join(str(x) for x in row) + ' |' for row in frame.itertuples(index=False,name=None)]
        return '\n'.join(lines)
    a = audit
    text = f'''# HeatShift data quality report

Built at {a['built_at_utc']}. These are measured counts from the active raw snapshots, not model results.

## Main counts

| Item | Count |
|---|---:|
| Original files, unchanged | {a['original_files']:,} |
| Original NOAA records | {a['raw_noaa_rows']:,} |
| Original Open-Meteo hourly rows | {a['raw_open_meteo_rows']:,} |
| Accepted unique NOAA readings | {a['clean_noaa_readings']:,} |
| Missing NOAA temperatures excluded | {a['rule_counts']['noaa_missing_temperature']:,} |
| Other rejected NOAA quality flags | {a['rule_counts']['noaa_quality_not_accepted']:,} |
| Alternative accepted reports at the same station/time | {a['alternative_noaa_reports']:,} |
| Selected times with conflicting accepted temperatures | {a['selected_times_with_conflicting_temperatures']:,} |
| Accepted NOAA readings without an exact 24-hour target | {a['excluded_missing_target']:,} |
| Labelled model examples across ALL partitions | {a['model_examples_total']:,} |
| Retained Open-Meteo context rows | {a['clean_open_meteo_rows']:,} |

Do not count the two sources as independent training examples. Open-Meteo is separate historical context.
The total model count includes reserve, replay and boundary exclusions; it is NOT the training count.
No model score was measured. None of the held-out target values was used to tune the preparation rules.

## Model examples by purpose and city

{table(splits)}

The target is a station temperature exactly 24 hours later. The input and target must both be accepted actual readings.
Optional past inputs remain blank in {a['missing_optional_lag24']:,} examples for the 24-hour lag and {a['missing_optional_lag48']:,} for the 48-hour lag, across all partitions. These counts can overlap.
Fit any replacement value using training rows only. Never fill the measured target.

## Station coverage

{table(coverage)}

Coverage is compared with every clock hour from 1 January to the final observed day of that year.
It does not mean every empty hour is a broken sensor: Karachi and Multan often report every three hours.
The partial 2025 files end on 24 August. No hourly observations were invented.

## Readiness

Recommended: enough for the first simple temperature prototype, subject to the limitations below.
The script passed {a['checks_passed']} processing checks. It also checked the SQLite database structure.
This is not a claim of accurate forecasts, health advice, a complete hourly prediction curve or full contest compliance.

'''
    text += '\n'.join('- '+x for x in a['limitations']) + '\n'
    (folder / 'QUALITY_REPORT.md').write_text(text,encoding='utf-8')

def ingest(input_dir):
    """First-time import only. Never silently replace or re-register raw bytes."""
    if (ROOT / 'manifest.json').exists():
        raise RuntimeError('Manifest already exists. Use python build_warehouse.py to rebuild. Do not overwrite raw data.')
    files = sorted(input_dir.glob('*.csv'))
    if not files:
        raise RuntimeError('No CSV input files found.')
    imported_at = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    manifest = []
    raw_dir = ROOT / '00_raw'
    raw_dir.mkdir(exist_ok=True)
    for path in files:
        first = path.read_text(encoding='utf-8-sig').splitlines()[0]
        is_open = first.startswith('latitude,longitude,')
        frame = pd.read_csv(path, skiprows=3 if is_open else 0, dtype=str, keep_default_na=False)
        if is_open:
            meta = pd.read_csv(path, nrows=1).iloc[0].to_dict()
            if float(meta['utc_offset_seconds']) != 0:
                raise ValueError('This import expects GMT/UTC Open-Meteo files; review offset before importing.')
            grid = (float(meta['latitude']), float(meta['longitude']))
            city = GRIDS[grid]
            source = 'open_meteo'
            name = f'open_meteo_{city.lower()}_2022_2024.csv'
            date = pd.to_datetime(frame['time'], utc=True, errors='raise')
            url = ''
            url_status = 'Unverified: exact original download URL and model setting were not supplied.'
            publisher = 'Open-Meteo; underlying model/provider Unverified in this CSV'
            licence = 'Open-Meteo data: CC BY 4.0; exact underlying model attribution needs original request.'
            licence_url = 'https://open-meteo.com/en/terms'
        else:
            ids = frame['STATION'].unique()
            if len(ids) != 1 or ids[0] not in STATIONS:
                raise ValueError(f'Unexpected station in {path.name}')
            city = STATIONS[ids[0]]
            date = pd.to_datetime(frame['DATE'], utc=True, errors='raise')
            years = date.dt.year.unique()
            if len(years) != 1:
                raise ValueError('Expected one station and year per NOAA file.')
            source = 'noaa'
            name = f'noaa_{ids[0]}_{years[0]}.csv'
            url = f'https://noaa-global-hourly-pds.s3.amazonaws.com/{years[0]}/{ids[0]}.csv'
            url_status = 'Candidate canonical URL inferred from station/year; not proof of original download or byte match.'
            publisher = 'NOAA NCEI, Integrated Surface Database / Global Hourly'
            licence = 'NOAA open data use terms; attribute NOAA and identify this package as modified data.'
            licence_url = 'https://registry.opendata.aws/noaa-isd/'
            meta = {}
        dest = raw_dir / name
        if dest.exists():
            raise ValueError(f'Raw filename collision: {name}')
        shutil.copyfile(path, dest)
        manifest.append(dict(raw_file=f'00_raw/{name}', original_filename=path.name, source=source,
                             city=city, publisher=publisher, sha256=sha(dest), bytes=dest.stat().st_size,
                             raw_rows=len(frame), event_start_utc=stamp(date.min()), event_end_utc=stamp(date.max()),
                             ingested_at_utc=imported_at, original_fetched_at_utc=None,
                             original_fetch_status='Unverified: not supplied; ingest time is NOT original download time.',
                             source_url=url, source_url_status=url_status, original_query=None,
                             model_setting='Unverified' if is_open else 'Not applicable: station observations',
                             licence=licence, licence_url=licence_url, export_metadata=meta))
    write_json(ROOT / 'manifest.json', manifest)

def assign_split(target):
    """Use the previously proposed target-date windows; do not tune them to scores."""
    result = pd.Series('outside_plan', index=target.index)
    windows = [('train', '2022-01-01', '2024-01-01'),
               ('validation', '2024-01-01', '2024-03-01'),
               ('calibration', '2024-03-01', '2024-04-01'),
               ('test_locked', '2024-04-01', '2024-10-01'),
               ('replay', '2024-10-01', '2025-01-01'),
               ('reserve_2025', '2025-01-01', '2026-01-01')]
    for label, begin, end in windows:
        start, stop = pd.Timestamp(begin, tz='UTC'), pd.Timestamp(end, tz='UTC')
        mask = target.ge(start) & target.lt(stop)
        result.loc[mask] = label
        if label != 'train':
            result.loc[mask & target.lt(start + pd.Timedelta(hours=24))] = 'boundary_gap'
    return result

def build():
    manifest = json.loads((ROOT / 'manifest.json').read_text(encoding='utf-8'))
    for item in manifest:
        if sha(ROOT / item['raw_file']) != item['sha256']:
            raise RuntimeError('Raw hash mismatch: ' + item['raw_file'] + '. Original data changed. Build stopped.')
    run_at = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    staging = Path(tempfile.mkdtemp(prefix='heatshift_build_'))
    for name in ['01_clean', '02_final', 'quality']:
        (staging / name).mkdir()
    actions, profiles, raw_noaa, raw_open, noaa_parts, open_parts = [], [], [], [], [], []
    rule_counts = {}

    def log(df, mask, field, rule, action, before=None, after=None):
        selected = df.loc[mask]
        rule_counts[rule] = rule_counts.get(rule, 0) + len(selected)
        for idx, row in selected.iterrows():
            actions.append(dict(raw_row_id=row['raw_row_id'], source_file=row['source_file'],
                                field=field, rule=rule, action=action,
                                before=str(before.loc[idx]) if before is not None else '',
                                after=str(after.loc[idx]) if after is not None else '',
                                processed_at_utc=run_at))

    for item in manifest:
        is_open = item['source'] == 'open_meteo'
        raw = pd.read_csv(ROOT / item['raw_file'], skiprows=3 if is_open else 0,
                          dtype=str, keep_default_na=False)
        d = pd.DataFrame(index=raw.index)
        d['raw_row_id'] = [item['sha256'] + ':' + str(i + 1) for i in raw.index]
        d['source_file'] = item['raw_file']
        d['source_record_number'] = raw.index + 1
        d['city'] = item['city']
        d['event_time_utc'] = pd.to_datetime(raw['time' if is_open else 'DATE'], utc=True, errors='coerce')
        d['ingested_at_utc'] = item['ingested_at_utc']
        invalid_time = d.event_time_utc.isna()
        log(d, invalid_time, 'event_time_utc', 'invalid_time', 'quarantine row')
        source_rows = pd.DataFrame({'raw_row_id': d.raw_row_id, 'source_file': d.source_file,
                                   'source_record_number': d.source_record_number,
                                   'payload_json': [json.dumps(x, sort_keys=True, ensure_ascii=False)
                                                    for x in raw.to_dict('records')]})
        (raw_open if is_open else raw_noaa).append(source_rows)
        if is_open:
            meta = item['export_metadata']
            d['grid_latitude'] = float(meta['latitude'])
            d['grid_longitude'] = float(meta['longitude'])
            d['grid_elevation_m'] = float(meta['elevation'])
            d['underlying_model'] = 'Unverified'
            d['historical_context_only'] = 1
            for old, (new, low, high) in FIELDS.items():
                if old not in raw:
                    raise ValueError(f'Missing expected Open-Meteo column: {old}')
                n = pd.to_numeric(raw[old], errors='coerce')
                missing = n.isna()
                invalid = n.notna() & ~n.between(low, high)
                log(d, missing, new, 'open_missing_' + new, 'leave missing', raw[old])
                log(d, invalid, new, 'open_range_' + new, 'set value missing; retain original in raw', raw[old])
                d[new] = n.mask(invalid)
            bad_dew = d.dew_point_c.gt(d.temperature_c + 0.2)
            log(d, bad_dew, 'dew_point_c', 'open_dew_above_air', 'set dew point missing', raw['dew_point_2m (°C)'])
            d.loc[bad_dew, 'dew_point_c'] = float('nan')
            open_parts.append(d.loc[~invalid_time].copy())
        else:
            if not {'STATION', 'TMP', 'REPORT_TYPE', 'LATITUDE', 'LONGITUDE'} <= set(raw.columns):
                raise ValueError('NOAA schema check failed.')
            d['station_id'] = raw.STATION
            d['station_name'] = raw.NAME
            d['station_latitude'] = pd.to_numeric(raw.LATITUDE, errors='raise')
            d['station_longitude'] = pd.to_numeric(raw.LONGITUDE, errors='raise')
            d['report_type'] = raw.REPORT_TYPE
            tmp = raw.TMP.str.split(',', expand=True)
            if tmp.shape[1] != 2:
                raise ValueError('Unexpected TMP encoding.')
            d['temperature_quality_code'] = tmp[1]
            encoded = pd.to_numeric(tmp[0], errors='coerce')
            missing = encoded.isna() | encoded.eq(9999)
            invalid_qc = ~tmp[1].isin(['0', '1', '4', '5']) & ~missing
            value = encoded / 10.0
            invalid_range = ~value.between(-93.2, 61.8) & ~missing
            log(d, missing, 'temp_c', 'noaa_missing_temperature', 'quarantine row; never fill target', raw.TMP)
            log(d, invalid_qc, 'temp_c', 'noaa_quality_not_accepted', 'quarantine row', raw.TMP)
            log(d, invalid_range, 'temp_c', 'noaa_temperature_out_of_range', 'quarantine row', raw.TMP)
            d['temp_c'] = value
            d['quality_rank'] = tmp[1].map({'1': 0, '5': 0, '0': 1, '4': 1}).fillna(9)
            d['report_rank'] = d.report_type.map({'FM-12': 0, 'FM-15': 1, 'FM-16': 2}).fillna(9)
            noaa_parts.append(d.loc[~(invalid_time | missing | invalid_qc | invalid_range)].copy())
        profiles.append({k: item[k] for k in ['raw_file', 'city', 'source', 'raw_rows', 'event_start_utc', 'event_end_utc']})

    noaa = pd.concat(noaa_parts, ignore_index=True)
    noaa = noaa.sort_values(['station_id', 'event_time_utc', 'quality_rank', 'report_rank',
                             'source_file', 'source_record_number'], kind='stable').reset_index(drop=True)
    keys = ['station_id', 'event_time_utc']
    groups = noaa.groupby(keys)
    noaa['accepted_reports_at_time'] = groups.temp_c.transform('size')
    noaa['conflicting_temperature_at_time'] = groups.temp_c.transform('nunique').gt(1).astype(int)
    repeated = noaa.duplicated(keys, keep='first')
    log(noaa, repeated, 'station_id,event_time_utc', 'multiple_accepted_reports_at_time',
        'exclude alternative; select quality rank then FM-12 then FM-15 then FM-16 then file/row')
    alternatives = noaa.loc[repeated].copy()
    noaa = noaa.loc[~repeated].drop(columns=['quality_rank', 'report_rank']).copy()
    noaa['row_id'] = 'noaa:' + noaa.station_id + ':' + noaa.event_time_utc.dt.strftime('%Y%m%dT%H%M%SZ')
    noaa['event_time_pk'] = noaa.event_time_utc.dt.tz_convert('Asia/Karachi').astype(str)
    op = pd.concat(open_parts, ignore_index=True).sort_values(['city', 'event_time_utc']).reset_index(drop=True)
    # Unseen ambiguous duplicates stop the build, rather than silently choosing values.
    if op.duplicated(['city', 'event_time_utc']).any():
        raise ValueError('Open-Meteo duplicate city/time; review original requests before combining.')
    op['row_id'] = 'open:' + op.city.str.lower() + ':' + op.event_time_utc.dt.strftime('%Y%m%dT%H%M%SZ')
    op['event_time_pk'] = op.event_time_utc.dt.tz_convert('Asia/Karachi').astype(str)

    # Timestamp joins, NOT row shifts. Sparse data make a 24-row shift incorrect.
    model = noaa[['row_id', 'raw_row_id', 'station_id', 'city', 'event_time_utc', 'temp_c']].rename(
        columns={'row_id': 'current_row_id', 'raw_row_id': 'current_raw_row_id', 'event_time_utc': 'prediction_time_utc'})
    for hours in [24, 48]:
        history = noaa[['station_id', 'event_time_utc', 'temp_c', 'row_id']].copy()
        history['event_time_utc'] += pd.Timedelta(hours=hours)
        history = history.rename(columns={'event_time_utc': 'prediction_time_utc', 'temp_c': f'temp_lag{hours}_c',
                                          'row_id': f'lag{hours}_row_id'})
        model = model.merge(history, how='left', on=['station_id', 'prediction_time_utc'], validate='one_to_one')
        model[f'lag{hours}_missing'] = model[f'temp_lag{hours}_c'].isna().astype(int)
    truth = noaa[['station_id', 'event_time_utc', 'temp_c', 'row_id', 'raw_row_id']].copy()
    truth['prediction_time_utc'] = truth.event_time_utc - pd.Timedelta(hours=24)
    truth = truth.rename(columns={'event_time_utc': 'target_time_utc', 'temp_c': TARGET,
                                  'row_id': 'target_row_id', 'raw_row_id': 'target_raw_row_id'})
    model = model.merge(truth, how='left', on=['station_id', 'prediction_time_utc'], validate='one_to_one')
    no_target = model.loc[model[TARGET].isna(), ['current_row_id', 'station_id', 'city', 'prediction_time_utc']].copy()
    no_target['reason'] = 'No accepted same-station measurement exactly 24 hours later. Do not fill.'
    model = model.loc[model[TARGET].notna()].copy()
    model['example_id'] = 'example:' + model.current_row_id
    model['baseline_temp_24h_c'] = model.temp_c
    model['hour_pk'] = model.prediction_time_utc.dt.tz_convert('Asia/Karachi').dt.hour
    model['month_pk'] = model.prediction_time_utc.dt.tz_convert('Asia/Karachi').dt.month
    model['split'] = assign_split(model.target_time_utc)
    model = model.sort_values(['prediction_time_utc', 'station_id']).reset_index(drop=True)

    # Comparison uses historical context; it is not a source of prediction features.
    comparison = noaa[['row_id', 'station_id', 'city', 'event_time_utc', 'temp_c']].merge(
        op[['row_id', 'city', 'event_time_utc', 'temperature_c', 'relative_humidity_pct']],
        how='inner', on=['city', 'event_time_utc'], suffixes=('_noaa', '_open'), validate='one_to_one')
    comparison['station_minus_grid_c'] = comparison.temp_c - comparison.temperature_c
    comparison['use'] = 'historical_context_only_not_model_input'

    # Missing hours are counted, never fabricated as observations.
    coverage = []
    for (city, year), rows in noaa.groupby(['city', noaa.event_time_utc.dt.year]):
        begin = pd.Timestamp(f'{year}-01-01', tz='UTC')
        end = min(pd.Timestamp(f'{year+1}-01-01', tz='UTC'), rows.event_time_utc.max().floor('D') + pd.Timedelta(days=1))
        expected = int((end - begin).total_seconds() / 3600)
        gaps = rows.event_time_utc.sort_values().diff().dt.total_seconds().div(3600)
        coverage.append(dict(city=city, year=int(year), accepted_unique_readings=len(rows),
                             calendar_hours_to_last_observed_day=expected, missing_hour_slots=expected-len(rows),
                             coverage_pct=round(100*len(rows)/expected,2),
                             median_spacing_hours=float(gaps.median()), largest_gap_hours=float(gaps.max()),
                             note='Hourly reference grid; scheduled 3-hour reports also leave empty hour slots.'))
    split_counts = model.groupby(['split', 'city']).size().unstack(fill_value=0).reset_index()
    check_rows = []
    def check(name, condition):
        if not bool(condition):
            raise AssertionError(name)
        check_rows.append(dict(check=name, result='PASS', checked_at_utc=run_at))
    check('raw hashes match supplied snapshots', all(sha(ROOT / i['raw_file']) == i['sha256'] for i in manifest))
    check('clean NOAA station/time unique', not noaa.duplicated(keys).any())
    check('clean Open-Meteo city/time unique', not op.duplicated(['city', 'event_time_utc']).any())
    check('NOAA observations are on the hour; no rounding used', noaa.event_time_utc.dt.minute.eq(0).all() and noaa.event_time_utc.dt.second.eq(0).all())
    check('all targets exactly 24 hours ahead', (model.target_time_utc-model.prediction_time_utc).eq(pd.Timedelta(hours=24)).all())
    check('target and required current temperature never filled', model[[TARGET, 'temp_c']].notna().all().all())
    check('model examples unique', model.example_id.is_unique)
    check('baseline equals current measured temperature', model.baseline_temp_24h_c.eq(model.temp_c).all())
    check('no Open-Meteo features in model contract', not any('open' in name or 'humidity' in name for name in FEATURES))
    check('future target never listed as an input', TARGET not in FEATURES)
    check('training labels stop before validation starts', model.loc[model.split.eq('train'), 'target_time_utc'].max() < model.loc[model.split.eq('validation'), 'prediction_time_utc'].min())
    for hours in [24,48]:
        lookup = noaa.set_index('row_id').event_time_utc
        matched_time = model[f'lag{hours}_row_id'].map(lookup)
        check(f'lag{hours} refers to same exact past time', (model.loc[matched_time.notna(), 'prediction_time_utc']-matched_time.dropna()).eq(pd.Timedelta(hours=hours)).all())
    nonempty = ['train','validation','calibration','test_locked','replay']
    check('each planned split has all three cities', all(model.loc[model.split.eq(s),'city'].nunique()==3 for s in nonempty))

    def export(frame, relative):
        out = frame.copy()
        for c in out.columns:
            if isinstance(out[c].dtype, pd.DatetimeTZDtype):
                out[c] = out[c].dt.strftime('%Y-%m-%dT%H:%M:%SZ')
        save_csv(out, staging / relative)
        return out
    nout = export(noaa, '01_clean/noaa_observations.csv')
    oout = export(op, '01_clean/open_meteo_context.csv')
    mout = export(model, '02_final/model_data.csv')
    cout = export(comparison, '02_final/historical_comparison.csv')
    for label in sorted(model.split.unique()):
        export(model.loc[model.split.eq(label)], f'02_final/{label}.csv')
    export(alternatives, 'quality/alternative_reports.csv')
    export(no_target, 'quality/rows_without_target.csv')
    action_frame = pd.DataFrame(actions, columns=['raw_row_id','source_file','field','rule','action','before','after','processed_at_utc'])
    export(action_frame, 'quality/cleaning_actions.csv')
    export(pd.DataFrame(coverage), 'quality/hour_coverage.csv')
    export(split_counts, 'quality/split_counts.csv')
    export(pd.DataFrame(check_rows), 'quality/checks.csv')
    export(pd.DataFrame(profiles), 'quality/input_profiles.csv')
    audit = dict(built_at_utc=run_at, status='PASS_WITH_DOCUMENTED_LIMITATIONS',
                 original_files=len(manifest), raw_noaa_rows=sum(i['raw_rows'] for i in manifest if i['source']=='noaa'),
                 raw_open_meteo_rows=sum(i['raw_rows'] for i in manifest if i['source']=='open_meteo'),
                 clean_noaa_readings=len(noaa), clean_open_meteo_rows=len(op),
                 alternative_noaa_reports=len(alternatives), selected_times_with_conflicting_temperatures=int(noaa.conflicting_temperature_at_time.sum()),
                 model_examples_total=len(model), excluded_missing_target=len(no_target),
                 examples_by_split={k:int(v) for k,v in model.split.value_counts().sort_index().items()},
                 missing_optional_lag24=int(model.lag24_missing.sum()), missing_optional_lag48=int(model.lag48_missing.sum()),
                 checks_passed=len(check_rows), rule_counts=rule_counts, model_trained=False,
                 data_quality_agent_status='Separate preserved agent in HeatShift_Unified_Space; this build performs deterministic cleaning',
                 limitations=['NOAA 2022-2023 supports training. Test dates remain fixed; 2025 is not used for training.',
                              'NOAA 2025 is reserve data, not extra training across the locked 2024 test.',
                              'Original Open-Meteo download time, request and model setting remain Unverified. NOAA has new verified during-event fetch receipts.',
                              'Station measurements are sparse. Not a complete 24-hour forecast curve.',
                              'Historical availability of station reports is unknown; replay assumes event-time availability.',
                              'This warehouse rebuild does not evaluate a model; current frozen-model evidence is in evidence/final_audit/primary_model.',
                              'Complete local-snapshot rebuild provided. Separate preserved agents and hourly orchestration are under HeatShift_Unified_Space and automation.'])
    write_json(staging / 'quality/summary.json', audit)
    quality_report(staging / 'quality', audit, split_counts, pd.DataFrame(coverage))
    contract = dict(status='Recommended. Check against your actually submitted declaration before model training.',
                    task='Same-station air temperature exactly 24 hours after prediction_time_utc',
                    features=FEATURES, target=TARGET, baseline='baseline_temp_24h_c = temp_c',
                    metric='MAE in Celsius on identical scored rows for model and baseline',
                    forbidden_inputs=['target_temp_24h_c','target_time_utc','target_row_id','target_raw_row_id','split','example_id',
                                      'current_raw_row_id','current_row_id','lag24_row_id','lag48_row_id','baseline_temp_24h_c'],
                    missing_values='Keep optional lags blank. Fit median imputation on train only during model training. Never fill target/current temperature.',
                    categories='Treat station_id, hour_pk and month_pk as categories in the model.',
                    split_rule='By target UTC time; 24-hour target gap at start of each later window. 2025 reserved.',
                    evaluation='Do not use test_locked, replay or reserve_2025 for choosing features, preprocessing or tuning.',
                    provenance='current/lag/target row IDs join clean NOAA; raw_row_id joins raw tables and file checksum plus record number.',
                    time_policy='Actual event UTC and real ingestion UTC remain separate. No invented original arrival times.')
    write_json(staging / '02_final/model_contract.json', contract)
    database = sqlite3.connect(staging / 'warehouse.sqlite')
    for name, frame in [('raw_noaa',pd.concat(raw_noaa,ignore_index=True)), ('raw_open_meteo',pd.concat(raw_open,ignore_index=True)),
                        ('clean_noaa',nout), ('clean_open_meteo',oout), ('gold_model',mout),
                        ('gold_historical_comparison',cout),('quality_actions',action_frame)]:
        frame.to_sql(name,database,index=False,if_exists='replace',chunksize=2000)
    dbmanifest = pd.DataFrame([{**i,'export_metadata':json.dumps(i['export_metadata'])} for i in manifest])
    dbmanifest.to_sql('source_manifest',database,index=False,if_exists='replace')
    database.executescript('''CREATE UNIQUE INDEX clean_noaa_key ON clean_noaa(row_id);
    CREATE UNIQUE INDEX clean_open_key ON clean_open_meteo(row_id);
    CREATE UNIQUE INDEX gold_example_key ON gold_model(example_id);
    CREATE INDEX gold_split ON gold_model(split);
    CREATE VIEW gold_train AS SELECT * FROM gold_model WHERE split='train';
    CREATE VIEW gold_validation AS SELECT * FROM gold_model WHERE split='validation';
    CREATE VIEW gold_calibration AS SELECT * FROM gold_model WHERE split='calibration';
    CREATE VIEW gold_test_locked AS SELECT * FROM gold_model WHERE split='test_locked';
    CREATE VIEW gold_replay AS SELECT * FROM gold_model WHERE split='replay';''')
    if database.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
        raise RuntimeError('SQLite integrity check failed.')
    database.close()
    # Publish only after validation. Previous outputs are preserved if processing fails above.
    for name in ['01_clean','02_final','quality']:
        dest = ROOT / name
        dest.mkdir(parents=True,exist_ok=True)
        for source in (staging/name).iterdir():
            target = dest/source.name
            temporary = target.with_name(target.name+'.next')
            shutil.copyfile(source,temporary)
            temporary.replace(target)
    # The database is the canonical published warehouse. Replace it last and atomically.
    temporary_database = ROOT / 'warehouse.sqlite.next'
    shutil.copyfile(staging / 'warehouse.sqlite',temporary_database)
    temporary_database.replace(ROOT / 'warehouse.sqlite')
    shutil.rmtree(staging)
    print(json.dumps(audit,indent=2))

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ingest',type=Path,help='First-time folder containing supplied CSV files only.')
    args = parser.parse_args()
    if args.ingest:
        ingest(args.ingest)
    build()
