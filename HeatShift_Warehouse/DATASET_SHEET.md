# Dataset sheet — HeatShift Pakistan

Prepared 19 October 2026. This describes the actual current snapshots.
User: an outdoor-work supervisor in Karachi, Lahore or Multan.
Task: predict station air temperature 24 hours after a known station reading. Units: degrees Celsius.
Scope: historical replay prototype. No illness prediction, work-safety certification or live forecasting claim.

| Item | NOAA station observations | Open-Meteo supplied historical export |
|---|---|---|
| Publisher | NOAA NCEI, ISD / Global Hourly | Open-Meteo; underlying model Unverified |
| Files | 12 station/year CSV files | 3 city/grid CSV files |
| Rows | 43,927 raw observations | 78,912 hourly rows |
| Period | 2022 to 24 August 2025 | 1 January 2022 to 31 December 2024 |
| Place | Karachi Jinnah, Lahore City, Multan International | Nearby grid cells; not the station's exact location |
| Source | https://registry.opendata.aws/noaa-isd/ | https://open-meteo.com/en/docs/historical-weather-api |
| Exact request | Verified URLs and station/year queries in manifest.csv | Original URL/settings Unverified; the CSV does not identify the selected model |
| Licence | NOAA open-data terms; attribution and no implied endorsement | CC BY 4.0 data terms; confirm underlying model attribution |
| Update rate | ISD archive is frozen after 24 August 2025 | Depends on original selected model; Unverified for these exports |
| Role | Model inputs and measured targets | Historical comparison only |
| Outside climate track list? | Yes | No |
| Collection proof | New fetch timestamps and SHA-256 receipts from this event | User supplied during event; original publisher download time/method still Unverified |

Combined raw record count: 122,839. This passes the guide's 50,000-row size option. These are not 122,839 independent training examples. See quality/summary.json for usable model counts and date partitions.

## Why these sources

NOAA supplies station observations with quality flags. Open-Meteo supplies an independent publisher's gridded historical product. They are not just two copies of the same CSV. Their underlying weather observations may overlap, so we do not claim statistical independence.

There is real engineering work: encoded units, suspect/missing temperatures, repeated reports, irregular reporting times and different station/grid locations. All raw bytes remain unchanged.

## Collection and permitted access

NOAA: documented public S3 downloads. All 12 requests succeeded and matched stored hashes. The 9 that overlapped the upload matched the user's supplied bytes. The original upload collection time is not retrospectively asserted.

Open-Meteo: original CSVs are preserved and reused locally. A fresh check found that the API host blocks crawlers in robots.txt, although its public docs describe API access. No new automated collection was performed here. Recover the original download method/settings and clarify any strict guide interpretation rather than claiming an access check passed.

Licence references:
- https://registry.opendata.aws/noaa-isd/
- https://open-meteo.com/en/terms

NOAA update notice:
https://www.nesdis.noaa.gov/news/service-location-change-integrated-surface-data-global-hourly

## Biases and limitations

- Three stations do not represent every neighbourhood or outdoor workplace.
- Many station hours have no report. Gaps remain visible.
- Historical arrival times are unavailable. Replay assumes readings are available at their event-time hour.
- NOAA has quality flags; Open-Meteo grid estimates are not equivalent to direct station measurements.
- Original Open-Meteo model is unknown. Do not call these supplied exports verified ERA5.
- This data is weather, not labelled worker-health outcomes.
- The final test covers selected 2024 months; report that limited evaluation coverage.

## Data handling

Raw: 00_raw plus manifest.csv/json. Original upload backup: evidence/original_uploads.zip.
Cleaned: one accepted station reading per station/time, plus a separate grid-context table.
Final: exact-time model examples, fixed chronological partitions and historical comparison tables.
No missing measured targets are filled. Optional older inputs remain blank for training-only preparation later.
All computed rows retain links back to source records.

## Outstanding evidence

- [ ] Original Open-Meteo URL, selected model, method and download time, where recoverable.
- [ ] Actual Dataset Declaration commit hash and timestamp.
- [ ] Human review of this document, source licences and AI-assisted code.

The warehouse has been built; full competition compliance cannot be certified while these evidence questions remain unresolved.
