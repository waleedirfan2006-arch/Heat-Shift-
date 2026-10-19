# HeatShift data quality report

Built at 2026-10-19T12:46:56Z. These are measured counts from the uploaded files, not model results.

## Main counts

| Item | Count |
|---|---:|
| Original files, unchanged | 12 |
| Original NOAA records | 34,719 |
| Original Open-Meteo hourly rows | 78,912 |
| Accepted unique NOAA readings | 30,539 |
| Missing NOAA temperatures excluded | 71 |
| Other rejected NOAA quality flags | 33 |
| Alternative accepted reports at the same station/time | 4,076 |
| Selected times with conflicting accepted temperatures | 1,571 |
| Accepted NOAA readings without an exact 24-hour target | 3,930 |
| Labelled model examples across ALL partitions | 26,609 |
| Retained Open-Meteo context rows | 78,912 |

Do not count the two sources as independent training examples. Open-Meteo is separate historical context.
The total model count includes reserve, replay and boundary exclusions; it is NOT the training count.
No model score was measured. None of the held-out target values was used to tune the preparation rules.

## Model examples by purpose and city

| split | Karachi | Lahore | Multan |
| --- | --- | --- | --- |
| boundary_gap | 30 | 66 | 28 |
| calibration | 183 | 398 | 174 |
| replay | 658 | 1068 | 644 |
| reserve_2025 | 1814 | 3339 | 1805 |
| test_locked | 1361 | 2620 | 1365 |
| train | 2720 | 3854 | 2699 |
| validation | 419 | 963 | 401 |

The target is a station temperature exactly 24 hours later. The input and target must both be accepted actual readings.
Optional past inputs remain blank in 2,457 examples for the 24-hour lag and 2,546 for the 48-hour lag, across all partitions. These counts can overlap.
Fit any replacement value using training rows only. Never fill the measured target.

## Station coverage

| city | year | accepted_unique_readings | calendar_hours_to_last_observed_day | missing_hour_slots | coverage_pct | median_spacing_hours | largest_gap_hours | note |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Karachi | 2023 | 2813 | 8760 | 5947 | 32.11 | 3.0 | 48.0 | Hourly reference grid; scheduled 3-hour reports also leave empty hour slots. |
| Karachi | 2024 | 2735 | 8784 | 6049 | 31.14 | 3.0 | 123.0 | Hourly reference grid; scheduled 3-hour reports also leave empty hour slots. |
| Karachi | 2025 | 1853 | 5664 | 3811 | 32.72 | 3.0 | 15.0 | Hourly reference grid; scheduled 3-hour reports also leave empty hour slots. |
| Lahore | 2023 | 5043 | 8760 | 3717 | 57.57 | 1.0 | 13.0 | Hourly reference grid; scheduled 3-hour reports also leave empty hour slots. |
| Lahore | 2024 | 6502 | 8784 | 2282 | 74.02 | 1.0 | 121.0 | Hourly reference grid; scheduled 3-hour reports also leave empty hour slots. |
| Lahore | 2025 | 4243 | 5664 | 1421 | 74.91 | 1.0 | 10.0 | Hourly reference grid; scheduled 3-hour reports also leave empty hour slots. |
| Multan | 2023 | 2800 | 8760 | 5960 | 31.96 | 3.0 | 48.0 | Hourly reference grid; scheduled 3-hour reports also leave empty hour slots. |
| Multan | 2024 | 2701 | 8784 | 6083 | 30.75 | 3.0 | 123.0 | Hourly reference grid; scheduled 3-hour reports also leave empty hour slots. |
| Multan | 2025 | 1849 | 5664 | 3815 | 32.64 | 3.0 | 15.0 | Hourly reference grid; scheduled 3-hour reports also leave empty hour slots. |

Coverage is compared with every clock hour from 1 January to the final observed day of that year.
It does not mean every empty hour is a broken sensor: Karachi and Multan often report every three hours.
The partial 2025 files end on 24 August. No hourly observations were invented.

## Readiness

Recommended: enough for the first simple temperature prototype, subject to the limitations below.
The script passed 14 processing checks. It also checked the SQLite database structure.
This is not a claim of accurate forecasts, health advice, a complete hourly prediction curve or full contest compliance.

- NOAA 2022 is absent. Planned training window stays 2022-2023; available training is 2023 only.
- NOAA 2025 is reserve data, not extra training across the locked 2024 test.
- Source download timestamps, exact Open-Meteo query and model setting remain Unverified.
- Station measurements are sparse. Not a complete 24-hour forecast curve.
- Historical availability of station reports is unknown; replay assumes event-time availability.
- No performance claim: model and fixed baseline have not been evaluated.
- Local snapshot rebuild only. Automated source collection and hourly orchestration are future steps.
