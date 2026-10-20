# Open-Meteo source review

**Status: partially verified. Original collection evidence is still required.**
The review is complete for available evidence. It cannot manufacture a missing download record.

## Verified from the unchanged CSV files

| City | Exported grid latitude / longitude | Elevation | Rows |
|---|---|---:|---:|
| Karachi | 25.00 / 67.25 | 25 m | 26,304 |
| Lahore | 31.50 / 74.25 | 217 m | 26,304 |
| Multan | 30.25 / 71.50 | 123 m | 26,304 |

Each file covers 2022-01-01 00:00 to 2024-12-31 23:00 UTC. Times are hourly, unique and complete in that interval. Metadata says GMT, offset zero.
The seven fields are temperature (C), relative humidity (%), dew point (C), surface pressure (hPa), cloud cover (%), wind speed (km/h) and shortwave radiation (W/m2).
Hashes match the manifests and snapshot ZIP. The audit found no missing values or violations of the existing broad ranges in these fields.
Open-Meteo is on the guide's track list. NOAA is outside it. Different publishers do not prove statistically independent weather products: reanalysis can assimilate station observations.

## Verified publisher documentation

- [Historical API documentation](https://open-meteo.com/en/docs/historical-weather-api): exported grid coordinates can differ from the requested coordinates. Model refresh rates differ. IFS is listed at six-hour intervals; ERA5/ERA5-Land daily with a five-day delay. The selected original model is unknown, so its refresh rate remains Unverified. Hourly rows do not mean hourly refreshes.
- [Licence](https://open-meteo.com/en/licence) and [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/): credit the supplier, link the licence and disclose changes.
- [Terms](https://open-meteo.com/en/terms): the free API has non-commercial access conditions and request limits. These access conditions are separate from the data licence.

Recommended chart attribution: “Weather data by Open-Meteo.com, CC BY 4.0. Processed by HeatShift; original exports retained. Selected underlying model Unverified.” Link the supplier and licence beside displayed data.

A published licence does not authenticate a specific uploaded CSV. The supplier identification follows the supplied export attribution; no original-request byte comparison is possible yet.

## Still unverified

| Detail | Required evidence |
|---|---|
| Original URL and query, including requested coordinates | Saved download URL, API request or collection script |
| Selected model and underlying dataset | Original request/model setting; do not guess ERA5 from the grid |
| Original download time | Timestamped original download record or fetch receipt with timezone |
| Collection method and its compliance | Collector record and applicable access/organiser guidance |
| Refresh rate of the original selected model | Identify that model first |

Original API robots evidence is retained in `../evidence/robots_checks.json`. The archive API returned `User-agent: *` and `Disallow: /` during the earlier check. The official site also provides API/CSV access. This does not establish how the team collected the files or settle the guide's interpretation. No new weather data were downloaded for this review.

## Exact steps to finish the missing evidence

1. The original downloader opens Chrome/Edge Downloads with Ctrl+J and searches the original filenames in `OPEN_METEO_EVIDENCE_TO_COMPLETE.csv`.
2. Copy each original download link if available. Save the visible download date/time and the record's timezone. For scripted downloads, use the original command/script and its execution log.
3. Store only relevant evidence in `HeatShift_Warehouse/evidence/open_meteo_collection/`. Do not publish account tokens, cookies or unrelated history.
4. Fill `OPEN_METEO_EVIDENCE_TO_COMPLETE.csv`. A statement written from memory must be labelled a collector statement, not a contemporaneous receipt. Unavailable facts stay Unverified.
5. Check request fields against the export's dates, variables, units and metadata. A similar URL does not prove the original request. File modification time, Git commit time and upload time are not publisher-download times.
6. After checking evidence, update BOTH manifest.json and manifest.csv for the corresponding files. Preserve original hashes/bytes. Run `python HeatShift_Warehouse/audit_data.py` again.
7. If original records are gone, ask organisers whether they accept the documented limitation or permit a new documented collection. Keep any new receipt separate; never backdate it or call it the old download. Clarify their robots rule before automated recollection.

Suggested organiser question (not sent): “Our unchanged Open-Meteo exports lack original download requests and timestamps. Can you accept the supplied metadata and hashes, or should we recollect? The documented archive API has a Disallow robots rule; which collection method does your guide permit?”

**Completion condition:** recovered and checked collection evidence, or explicit organiser acceptance of the limitation/permitted replacement. Until then this part is not fully verified.
