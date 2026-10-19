# Dataset Declaration — HeatShift Pakistan

Status: DRAFT prepared on 19 October 2026 after the noon PKT deadline.
This file is not proof of a timely submission. Preserve any declaration already committed. Do not backdate this draft.
Team name: TO FILL.
Repository URL, supplied by the user: https://github.com/waleedirfan2006-arch/Heat-Shift-
Team size: 3; user confirmed this is allowed.
Track: Climate and heat-health.

## User and problem

HeatShift supports outdoor-work supervisors in Karachi, Lahore and Multan. The prototype predicts station air temperature 24 hours after a known observation and explains historical conditions with evidence. It is a historical replay, not a live health-warning service.

## Sources

1. NOAA NCEI Integrated Surface Database / Global Hourly. Public source: https://registry.opendata.aws/noaa-isd/ . Station IDs: 41780099999, 41640099999 and 41675099999. Twelve station/year files cover 2022–2025, with 2025 ending on 24 August. Exact verified URLs, queries, fetch times and hashes are in manifest.csv. Use follows NOAA open-data terms with attribution and no implied endorsement. The ISD archive no longer updates after 24 August 2025; the pipeline will replay history.

2. Open-Meteo historical CSV exports for grid coordinates 25.00N/67.25E, 31.50N/74.25E and 30.25N/71.50E. Publisher documentation: https://open-meteo.com/en/docs/historical-weather-api . Data terms: https://open-meteo.com/en/terms (CC BY 4.0). Files cover 2022–2024. Exact original request, selected model, update rate for that model and publisher download time remain Unverified. The files were supplied by the team during the event. We will not claim these details are known without supporting records.

NOAA ISD is the credible source outside the climate track's named list. The two publishers provide station and gridded products; they are not simply duplicate downloads. Their underlying observations may overlap.

## Actual volume and roles

43,927 raw NOAA records plus 78,912 Open-Meteo rows = 122,839 source records. This is source volume, not the number of training examples. Usable counts are printed by make data and stored in quality/summary.json.
NOAA supplies model inputs and measured answers. Open-Meteo is separate historical comparison data and never fills missing station targets or supplies future-known model inputs.

## Baseline fixed before model results

For a station at time t, predict its temperature at t + 24 hours to equal its measured temperature at t.
The main score is MAE: average absolute error in Celsius. Compare the model and baseline on identical eligible rows. Lower MAE is better. We do not promise an improvement.
No prediction model has been trained or scored in this package.

## Recommended model and date plan

Ridge regression with current temperature, temperatures 24 and 48 hours earlier, station, hour and month. Fit all learned preparation on training data only.
By target UTC date: train 2022–2023; validate January–February 2024; calibrate uncertainty in March 2024; lock April–September 2024 for final testing; reserve October–December 2024 for replay. Use 24-hour boundary gaps. Keep 2025 as reserve, not extra training for the 2024 test.

## Integrity and remaining disclosure

Preserve raw bytes, hashes, source receipts and transformation logs. Do not fill targets, invent measurements, fabricate logs or use test results for tuning. Show gaps and station coverage limits.
Source metadata gaps and access-method questions are recorded in DATASET_SHEET.md. Material AI assistance is disclosed in AI_Use_Log.md. The Data Quality Agent, model evaluation, hourly schedule and deployed assistant are not yet implemented.

## Submission evidence — team must fill truthfully

Original declaration commit hash: UNVERIFIED.
Original declaration committed at: UNVERIFIED.
Any organizer-approved late submission/change: UNVERIFIED; do not assume approval.
The user reported dataset commit 8f3e9f1 and merged PR #1. That report alone does not prove that a Dataset Declaration was included or committed before noon; inspect the actual declaration's history.
