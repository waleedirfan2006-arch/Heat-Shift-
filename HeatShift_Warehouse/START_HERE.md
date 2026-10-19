# HeatShift: Step 2 is built

A data warehouse is one organised place for your data.
This package has the original files, cleaned tables and final model tables.
It also has `warehouse.sqlite`: the same tables in one database file.
No paid service or account is needed. No model has been trained yet.

## 1. What is inside?

| Place | Simple meaning | What to do |
|---|---|---|
| `00_raw/` | Your 12 original files. Only filenames were made clearer. File contents are unchanged. | Never edit them. |
| `01_clean/noaa_observations.csv` | Accepted station temperature readings. One reading per station and time. | Use for station charts and building examples. |
| `01_clean/open_meteo_context.csv` | Clean historical grid estimates. A grid is a small area used by a weather model. | Use for separate historical comparison. |
| `02_final/train.csv` | Examples the model may learn from. | Start model training with this file. |
| `02_final/validation.csv` | Separate examples for checking model choices. | Use to choose model settings. |
| `02_final/calibration.csv` | Separate examples for estimating an error range. | Use after choosing the model. |
| `02_final/test_locked.csv` | Unseen examples for the final fair score. | Do not use to choose settings or fill missing values. |
| `02_final/replay.csv` | Old records for the historical demo. | Show their real historical dates. |
| `02_final/reserve_2025.csv` | Extra later data kept aside. | Do not add it to training while testing on 2024. |
| `02_final/boundary_gap.csv` | Examples left out at date boundaries. | Do not train or score on them. |
| `02_final/model_data.csv` | All labelled examples, with a `split` column showing each purpose. | Never randomly split or train on this whole file. |
| `02_final/historical_comparison.csv` | Station temperature beside the historical grid temperature. | Not an input to the prediction model. |
| `quality/` | Counts, gaps, exclusions, alternative reports and checks. | Read `quality/QUALITY_REPORT.md` first. |
| `manifest.json` | A record of each source file and its fingerprint. | Complete missing original download details honestly. |

## 2. How was it cleaned?

All choices below are **Recommended**. They are recorded in the Python script.

1. Keep the original file bytes unchanged.
2. Read each file's actual dates. Do not guess the year from names like `(1)`.
3. Convert NOAA's encoded temperature to Celsius. For example, `+0095,1` means 9.5 C with quality code 1.
4. Exclude a missing temperature code, a rejected quality code or a value outside NOAA's documented temperature range.
5. Keep quality codes 0, 1, 4 and 5. These are the chosen conservative allowed codes. Other codes remain in raw data for review.
6. When several accepted reports share a station and time, prefer stronger quality checks, then report type FM-12, FM-15, FM-16, then file/row order. FM codes identify report formats. This priority is a project choice, not proof one report is always right.
7. Flag different temperatures reported at the same time. Keep the alternatives in `quality/alternative_reports.csv`. Do not average them into an invented observation.
8. Read Open-Meteo's first metadata lines separately. Metadata means information about the file, such as its location and time zone.
9. Check Open-Meteo numbers, ranges and humidity. Leave missing or rejected values blank. No missing observations are invented.
10. Store times in UTC, the common world time standard. Also provide Pakistan time where useful.
11. Keep historical event time separate from the time this warehouse imported the file.

`quality/cleaning_actions.csv` records exclusions and flagged values, their source rows, rules and processing times. Ordinary column renaming and unit decoding are explained here and in the script. No learned cleaning or model fitting has happened.

## 3. What is the final data?

Each model row is one example:

**Temperature now + temperature 24 and 48 hours ago + station + hour + month → measured temperature 24 hours later.**

The right side is the answer used to teach and test the model. It is not an input.
During a real prediction, that answer is not known yet.

Rows are joined using exact times and the same station. A 24-row shift is wrong when readings are not hourly.
If the temperature exactly 24 hours later is missing, that example is excluded.
If an older input is missing, it stays blank with a missing-value marker. Later, fit its replacement value using training data only.
The baseline is fixed: tomorrow at this hour is predicted to equal the temperature now.
A baseline is a simple prediction that the model should try to beat.

Read `02_final/model_contract.json` for the exact input list. Do not feed every numeric column into the model.

## 4. Is the data enough?

It is enough to start a simple three-city temperature prototype. It does not prove good predictions.
Read `quality/QUALITY_REPORT.md` for the measured usable counts.
Recommended model: Ridge regression, a simple model that learns a weighted combination of inputs.
Compare its errors against the fixed baseline on the same test examples.

The actual station files cover 2023 to 24 August 2025. Open-Meteo covers 2022 to 2024.
The earlier plan had NOAA training in 2022–2023. NOAA 2022 was not among these uploads.
The planned date boundaries are retained. The available training examples therefore come from 2023 only.
No test dates were moved to improve a result. No result has been calculated.
Recommended: obtain the three missing NOAA 2022 files before training if your submitted declaration promised them. Otherwise record the missing year and resolve any declaration change with the organisers.

The station readings have many empty hours. This version predicts the next day's same-time temperature where usable station data exist. It does not yet provide a complete 24-hour curve.
It cannot predict illnesses, guarantee safe working hours or demonstrate an accurate live forecast for today.

## 5. How do we use it?

1. Extract the ZIP.
2. Open `quality/QUALITY_REPORT.md` and the CSV tables. Excel can open CSV files. Treat station IDs as text; do not save over original files from Excel.
3. Keep `test_locked.csv`, `replay.csv` and `reserve_2025.csv` out of model tuning.
4. Use `train.csv` for the next step: train the simple model.
5. Your web teammate can query `warehouse.sqlite` with Python's built-in `sqlite3`.

The warehouse is already built. To recreate it, open a terminal in this folder:

```bash
python -m pip install -r requirements.txt
python build_warehouse.py
```

On Windows, use `py` instead of `python` if needed. On Linux, `python3` may be the command.
If Make is installed, `make data` runs the same build.
The build checks raw file fingerprints first. It stops if the originals have changed.
It works from the included local snapshots. It does not download files or run hourly yet.
Do not run two rebuilds at the same time.
Do not edit cleaned/final files manually: a rebuild replaces them. Change reviewed rules in the script instead.

Example database query:

```sql
SELECT split, city, COUNT(*) AS examples
FROM gold_model
GROUP BY split, city;
```

## 6. Things still needed

- Original download times and exact Open-Meteo request/model setting were not supplied. They are marked **Unverified**. A file's local modification time is not proof of a download time.
- We have not called these Open-Meteo uploads ERA5. The CSV does not prove which model was selected.
- Source URLs inferred from station/year are candidate URLs, not proof of where these exact bytes were fetched.
- Keep source and licence acknowledgements. See `SOURCES_AND_RULES.md`.
- Automated collection, the hourly schedule, drift checks, the AI assistant and the dashboard are later steps. This package does not claim the whole competition system is complete.
- The word `locked` is a team rule, not file encryption. All supplied historical readings are still present in raw data.

## Small glossary

CSV: a plain table file that Excel and Python can read.
SQLite: a free database stored in one file.
Row: one record in a table.
Feature: an input used by the model.
Target: the measured answer the model tries to predict.
Training: learning from examples.
Validation: checking model choices on separate examples.
Test: the final check using examples not used for choosing the model.
Calibration: estimating a prediction's error range from separate examples.
Replay: a demo that processes old records in time order.
Missing value: a measurement that is not available.
Fingerprint / SHA-256: a code that changes when a file's bytes change.
Provenance: the record of where data came from.
Leakage: giving the model information that would not be known when predicting.
MAE: the average size of prediction errors, measured here in degrees Celsius.
