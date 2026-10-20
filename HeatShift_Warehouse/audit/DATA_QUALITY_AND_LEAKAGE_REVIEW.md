# Data quality and leakage review

Base repository: ffdecac496688f8257741f69ac61d693be53ace2.
Actual timestamps, file hashes and runtime versions are in `audit_results.json`.

**Verdict: structural audit passed, with limitations.**
The inspected data/code show no future-value joins, overlapping examples or preprocessing fitted outside training. This cannot certify unknown historical report availability or live accuracy.
No model was trained or scored. Held-out rows were inspected for structural integrity only. No test-based rule or threshold was chosen.

## Measured results

| Item | Count |
|---|---:|
| Raw files | 15 |
| NOAA raw records | 43,927 |
| Open-Meteo rows | 78,912 |
| Clean unique NOAA observations | 39,305 |
| Training examples (2022–2023) | 16,463 |
| Validation / calibration examples | 1,783 / 755 |
| Locked test / replay examples | 5,346 / 2,370 |
| Reserved 2025 / excluded boundary examples | 6,958 / 124 |
| Structural checks passed | 211 |
| Guard stress tests passed | 10 |

All 11 clean/final CSVs were reproduced byte-for-byte in a fresh destination. SQLite integrity was `ok`. See `rebuild_verification.json`.

## Checks and evidence

| Area | Check |
|---|---|
| Source integrity | Manifest file sets, hashes, snapshot ZIP, counts, time bounds and metadata |
| Quality | Schemas, units, NOAA temperature decoding/QC, broad ranges and missing fields |
| Cleaning | Independently reconstruct NOAA duplicate priority and Open-Meteo cleaning |
| Provenance | Current values, lags and targets resolve to original station readings |
| Time leakage | Same-station exact -24h/-48h inputs, +24h targets, PKT calendar features |
| Partitions | Independently reconstruct all date splits; no duplicate examples across files |
| Boundary separation | Previous labels occur before the next partition's issue times |
| Baseline | Exactly the current observed temperature for every example |
| Training | Explicit feature allowlist, chronological folds, imputer/scaler inside fitted pipeline |
| Completeness | Every eligible current/+24h pair appears once; missing-target exclusions reconcile |

`audit_checks.csv` contains every check. Other CSVs show raw missing/range counts, city/year coverage, partition counts and training-only profiles.

## Important findings and limits

- NOAA has 110 missing temperatures and 47 other excluded QC records. There are 4,465 alternative accepted reports and 1,718 selected times with conflicting temperatures. The existing priority rule is reproducible, not proof the chosen report is correct. Alternatives remain available.
- Training has 1,517 missing 24-hour lags and 1,594 missing 48-hour lags. Counts overlap. Replacement medians are fitted on training only; required current/target values are never filled.
- Karachi and Multan often report every three hours. Their annual hourly-reference coverage is roughly 28–33%. Some gaps are 123 hours. No hourly observations were invented.
- Requiring an actual +24h target excludes 5,506 current readings. Scores will describe available observation pairs, not all hours or locations. City reporting coverage is unequal.
- Validation is January–February and calibration March. They do not alone establish summer performance. Keep declared windows fixed and disclose the seasonal limitation.
- Some old observations legitimately reappear later as past inputs: 39 training target records occur as validation 48-hour lags. At those later issue times they are past information. This is not overlapping examples.
- Actual historical report arrival times and subsequent archive revisions are unknown. Strict real-time/as-of-time leakage cannot be ruled out. Describe this as retrospective evaluation assuming event-time availability, not validated live forecasting.
- Open-Meteo is historical context only. Do not use it to fill NOAA inputs/targets. Its original model, request, collection method and fetch time remain unverified.
- The live demo uses Open-Meteo grid estimates with a NOAA-station-trained model. That combination is unvalidated. A nearby grid cell is not the same measurement as a station. Keep the demo warning or use clearly labelled historical replay.
- Existing scores and saved model use the older 9,273-example training dataset; the older Ridge result did not beat the baseline. They are not updated-data results.
- A code/data review cannot prove nobody previously examined test results, certify unseen teammate work, or establish a missing declaration deadline receipt. The guide's compliance depends on evidence beyond these data checks.
- No personal-data fields were identified in the used weather tables. This is not a forensic privacy audit of every unused raw payload field.

## Fixes included

- Reproducible independent `audit_data.py` and reports.
- New `validate_data.py` rejects invalid training/validation partitions, dates, horizons, duplicate keys, baseline changes and incorrect missing/calendar flags before training.
- `train_model.py` now calls those guards, derives the training date range from data and records input hashes/time in future reports. Model candidates/settings remain unchanged.
- Guard tests damage copies in memory only. They are labelled synthetic stress tests, never model evaluation.
- `.gitattributes` preserves raw bytes across Windows/Linux. `.gitignore` excludes generated caches and SQLite artifacts.
- Manifests include verified source documentation and attribution without invented original collection details.

The warehouse replaces CSVs individually and SQLite last. The CSV group is not a single transaction. Mateen should use one published database/version consistently and implement last-good handling. This audit is not his Data Quality Agent.

## Run from repository root

Recommended: Python 3.12 and a virtual environment.

```bash
python -m pip install -r HeatShift_Warehouse/requirements.txt -r HeatShift_Training/requirements.txt
python HeatShift_Warehouse/audit_data.py
python HeatShift_Training/test_data_guards.py
python HeatShift_Warehouse/pipeline.py --output ../HeatShift_Audit_Rebuild
```

Use `py` on Windows if needed and a new empty rebuild destination. The runtime used for this audit is recorded honestly (including scikit-learn 1.8.0; repository training requirements pin 1.6.1). These checks do not establish model performance under either version. Run on the team's installed environment before training.

Amaan handles evidence and integration. Mateen builds runtime agents. Waleed reviews these small guard/report changes and handles model training, uncertainty and final evaluation. No training was performed in this review.
