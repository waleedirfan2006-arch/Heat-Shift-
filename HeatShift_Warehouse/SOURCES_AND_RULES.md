# Sources and Recommended rules

This is a Step 2 warehouse of the 12 files uploaded by the team. It does not certify all contest requirements.
Original files were copied unchanged. Derived files must be described as modified data.

## Checked documentation

Checked on 19 October 2026:

- NOAA ISD format documentation, air-temperature and quality-code sections (printed pages 10–11): https://www.ncei.noaa.gov/pub/data/noaa/isd-format-document.pdf
- NOAA Global Hourly overview: https://www.ncei.noaa.gov/products/land-based-station/integrated-surface-database
- NOAA retirement notice: https://www.nesdis.noaa.gov/news/service-location-change-integrated-surface-data-global-hourly
- Open-Meteo historical data documentation: https://open-meteo.com/en/docs/historical-weather-api

The NOAA document defines encoded temperature / 10, missing code +9999, Celsius and quality flags. The accepted air-temperature range is -93.2 to +61.8 C.
Choosing quality codes 0/1/4/5 and preferring FM-12 among equivalent-quality reports are Recommended project rules, not additional NOAA requirements.
Open-Meteo range checks are broad Recommended sanity checks. They do not prove measurement accuracy. A dew point over air temperature by more than 0.2 C is flagged; this tolerance is a Recommended rounding allowance.

NOAA's 2026 retirement notice says ISD has no updates after 24 August 2025. This matches the final dates of the team's 2025 files. Historical replay remains possible. A current station feed would require a separate integration, such as NOAA's successor GHCNh; it is not included here.

Open-Meteo's archive contains model-derived historical weather. Its CSV metadata here do not identify the model or original request. The final comparison table therefore says Open-Meteo, not verified ERA5. Different publishers do not mean their underlying observations are statistically independent.

## Attribution and provenance

NOAA attribution: NOAA National Centers for Environmental Information, Integrated Surface Database / Global Hourly. This package contains processed versions; no NOAA endorsement is implied.
Terms reference: https://registry.opendata.aws/noaa-isd/

Open-Meteo attribution: weather data provided by Open-Meteo.com, processed by the HeatShift team. The public data terms specify CC BY 4.0. Confirm the selected underlying data provider/model from the original export request and add any required credit.
Terms reference: https://open-meteo.com/en/terms

Exact original download URLs, query settings and fetch times remain Unverified unless the team supplies its download records. No raw hash is claimed to match a new online download.
The manifest records actual local ingestion time and a SHA-256 fingerprint for every supplied file. It deliberately leaves unknown original fetch times blank.

## Frozen date windows from the earlier playbook

Recommended; check against the declaration actually submitted by the team.

| Target time in UTC | Purpose |
|---|---|
| 2022–2023 | Train; only 2023 NOAA is available in these uploads |
| January–February 2024 | Validation |
| March 2024 | Calibration |
| April–September 2024 | Locked final test |
| October–December 2024 | Replay demonstration |
| 2025 | Extra reserve; not training for the 2024 evaluation |

The first 24 hours of each later window are excluded as a boundary gap. Example: validation targets start 2 January 2024 at 00:00 UTC. Their current input is 1 January at 00:00 UTC, after the end of the training target window. Older past inputs may correctly fall in a previous window; they are not future information.
Target time is exactly 24 hours after prediction time. Known timestamps and missingness checks do not involve evaluating model accuracy on the locked test.

Original arrival times are unknown. Replay assumes that each measurement is available at its event-time hour. This is a historical simulation assumption, not verified live-delivery performance. Historical Open-Meteo values never enter prediction features or fill station targets.
