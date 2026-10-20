---
title: HeatShift Pakistan Temperature Demo
emoji: 🌤️
colorFrom: blue
colorTo: yellow
sdk: static
app_file: index.html
pinned: false
---

# HeatShift: 24-hour temperature estimate

Choose Karachi, Lahore, or Multan. Enter the latest on-the-hour airport METAR temperature and its observation time in Pakistan Standard Time (PKT). The page retrieves the JMA GSM previous-day forecast inputs and runs the same frozen HistGradientBoosting model used by the Python demo. It compares the estimate with the persistence baseline (tomorrow equals the observed temperature).

This folder uses Hugging Face's static SDK. Aviation Weather Center does not allow browser cross-origin API requests, so the current METAR temperature must be entered manually. The model and JMA data remain the same; the observation source and entry are made explicit.

This is an experimental student project, not an exact answer, official forecast, or weather warning. Weather predictions have unavoidable error. The model does not learn from requested predictions.

## Model evidence

The frozen model was trained on 16,463 NOAA station examples from 2022–2023. Selection used chronological training folds. Fixed January–February 2024 validation MAE (model vs persistence) was Karachi **1.031 vs 1.397 °C**, Lahore **1.082 vs 1.131 °C**, and Multan **1.226 vs 1.355 °C**. On the 2024 locked test it scored Karachi **0.932 vs 0.892 °C**, Lahore **1.488 vs 1.923 °C**, and Multan **1.469 vs 1.896 °C**. Karachi did not beat the baseline on that test. On the separate 2025 reserve it scored Karachi **0.946 vs 1.033 °C**, Lahore **1.433 vs 1.857 °C**, and Multan **1.465 vs 1.866 °C**. Untuned external 2026 checks scored Karachi **0.923 vs 0.932 °C** (176 METAR pairs), Lahore **1.190 vs 1.373 °C** (789 strict-quality NOAA GHCNh pairs), and Multan **1.431 vs 1.613 °C** (530 strict-quality NOAA GHCNh pairs). The Karachi and Multan 2026 uncertainty intervals include no gain. The 2026 sources and periods differ by city, so they are not one comparable three-city score. These checks did not change or tune the model.

Predictions are not guaranteed. The approximate 90th-percentile error bands use training-only errors and are not guarantees of coverage.

## Sources

- Current temperature: [Aviation Weather Center METAR data](https://aviationweather.gov/data/metar/). The browser cannot query its API directly, so the current temperature is entered by the user.
- JMA GSM previous-day forecast inputs: [Open-Meteo Previous Model Runs API](https://open-meteo.com/en/docs/previous-runs-api), CC BY 4.0.
- The target is the selected city's airport-station temperature 24 hours after the entered observation time.

## Files

- `index.html`: static user interface and JMA API request.
- `model.json`: exported frozen model parameters.
- `model.js`: JavaScript model inference.
- `export_model.py`: regenerate `model.json` from the frozen joblib artifact.


## Interactive update

The workspace supports pasted station reports, Celsius/Fahrenheit, dark mode, baseline-only mode, five session comparisons and downloadable receipts. Entered observations must be exact-hour reports from the last four hours. The new station-only training experiment is documented in REVIEW.md; it was not promoted because it did not beat validation persistence. Copy all deployment files together.
