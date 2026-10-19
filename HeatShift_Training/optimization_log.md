# HeatShift model optimization log

This log records model experiments using the supplied training and validation data. The locked test data, replay data and 2025 reserve data were not used.

## Data sources and how they were used

- **NOAA Global Hourly** provides the measured station temperatures used as training answers and validation truth. The uploaded NOAA station files do not include 2022, so the existing date split gives the model NOAA training examples from 2023 only.
- **Open-Meteo** provides hourly historical grid estimates for 2022–2024. Its files match every model example's city and prediction time: 9,273 training rows and 1,783 validation rows. These estimates are not the same thing as the NOAA station measurements, and the original Open-Meteo model/provider is unverified.
- Open-Meteo was tested as **same-time input context only**. No later-hour Open-Meteo values were used. Its values were not used as NOAA training answers or to fill missing NOAA station temperatures.

## Measured results

All values below are mean absolute error (MAE) in degrees Celsius on the same 1,783 validation examples. Lower is better.

| Experiment | Validation MAE | Change from fixed baseline |
|---|---:|---:|
| Fixed baseline: tomorrow equals today's NOAA temperature | **1.2352** | — |
| Existing Ridge temperature-change model | 1.3208 | 0.0856 worse |
| Ridge with extended regularization search, NOAA inputs only | 1.2674 | 0.0322 worse |
| Ridge with extended search and Open-Meteo current temperature | 1.2609 | 0.0257 worse |
| Ridge with extended search and all tested Open-Meteo weather fields | 1.2660 | 0.0308 worse |
| HistGradientBoosting, NOAA inputs only | 1.2560 | 0.0208 worse |
| HistGradientBoosting with Open-Meteo weather fields | 1.2577 | 0.0225 worse |
| GradientBoosting with Open-Meteo weather fields | 1.2604 | 0.0252 worse |

The extended Ridge search selected alpha 1,000 for the Open-Meteo variants. On training-only chronological folds, the best tested Ridge-with-Open-Meteo setup had MAE 1.4477 °C, while the fixed baseline scored 1.3792 °C on those same folds. Thus the added fields did not justify changing the model.

## NOAA station weather fields

The raw NOAA records also contain dew point, sea-level pressure and wind. We decoded these only for the training rows and validation rows, joining by the existing raw-row reference. NOAA documents these as station observations with value and quality fields in its [ISD format guide](https://www.ncei.noaa.gov/pub/data/noaa/isd-format-document.pdf). The experiment kept values with quality codes 0, 1, 4 or 5, and fit missing-value replacement on each training fold.

Coverage was uneven: dew point was present in 7,641/9,273 training rows and 1,391/1,783 validation rows; sea-level pressure in 6,987/9,273 and 1,053/1,783; wind speed in 7,674/9,273 and 1,403/1,783.

| Experiment | Training-fold MAE | Validation MAE |
|---|---:|---:|
| Fixed baseline | **1.3792** | **1.2352** |
| Ridge with NOAA weather fields | 1.4017 | 1.2573 |
| HistGradientBoosting with NOAA weather fields | 1.6217 | 1.2608 |
| GradientBoosting with NOAA weather fields | 1.4414 | 1.2597 |

The scores are all worse than the baseline on both training folds and validation, so the extra station fields were not added to the model contract.

## City-by-city Ridge fallback

We also selected the existing Ridge alpha using training-only chronological folds (alpha 100), then compared Ridge with persistence separately by city across those folds. Ridge was worse in every city's training folds, so the rule selected persistence for Karachi, Lahore and Multan. On validation, that policy scored 1.2352 °C, exactly matching the fixed baseline. Although Ridge had a small validation-only advantage in Karachi, the training folds did not support using it there, so that result was not used to change the policy.

## Archived forecast experiment (GFS, 24-hour lead)

We checked Open-Meteo's Previous Model Runs API, which provides `temperature_2m_previous_day1`: the forecast for each valid hour made 24 hours earlier. This is archived forecast input, unlike reanalysis or historical weather estimates. The API's documentation identifies NCEP GFS as an available global model and says its 2 m temperature archive extends back to March 2021. Sources: [Previous Model Runs API](https://open-meteo.com/en/docs/previous-runs-api) and [GFS API](https://open-meteo.com/en/docs/gfs-api). The experiment requested `models=gfs_seamless`, `hourly=temperature_2m_previous_day1`, and UTC timestamps for the three existing Open-Meteo city grid coordinates; it joined each value to the NOAA target by city and `target_time_utc`.

Coverage was 9,222/9,273 training rows (99.5%) and 1,329/1,783 validation rows (74.5%). Missing archived forecasts were left out, not filled. All comparisons below use the same covered rows within each split:

| Experiment | Training-only chronological-fold MAE | Validation MAE |
|---|---:|---:|
| Persistence baseline, matched rows | 1.3792 | 1.3378 |
| Raw GFS 24-hour forecast | — | 2.3141 |
| OLS bias-corrected GFS/persistence blend | 1.9322 mean across folds | 1.3097 |

The exploratory blend used training data only and combined current NOAA temperature, the difference between GFS and current temperature, city, and Pakistan-local hour/month cycles. Its chronological fold MAEs were 2.3465, 2.2192, and 1.2309 °C, compared with baseline fold MAEs of 1.7898, 1.2512, and 1.0959 °C. The small validation improvement is not supported by the chronological training checks, and almost one quarter of validation rows lack archived GFS values. **Do not select or promote this blend.** The locked test, replay, and 2025 reserve data were not used.

## Decision

Keep the existing Ridge model for comparison and report honestly that it has not beaten the baseline. The city-by-city fallback and archived GFS experiment also did not establish a reliable improvement. Do not describe Open-Meteo historical estimates as independent station observations or as a verified live forecast feed. The current contract continues to use NOAA station readings for targets and the declared temperature, lag, station and time inputs for the model.

The next data improvement is to obtain the missing NOAA 2022 station files if the submitted dataset plan promised them. Do not substitute Open-Meteo grid estimates for those missing station measurements. Revisit additional inputs only after confirming that the same input data would be available at prediction time in the deployed app.

