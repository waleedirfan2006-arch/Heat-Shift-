---
title: HeatShift Pakistan Temperature Demo
emoji: 🌤️
colorFrom: blue
colorTo: orange
sdk: gradio
python_version: 3.10
app_file: app.py
pinned: false
---

# HeatShift: 24-hour temperature estimates

Choose Karachi, Lahore, or Multan to estimate the selected airport station's temperature at the same hour tomorrow. The demo uses a current METAR observation, the archived JMA forecast for the target hour, and a pooled model trained on NOAA observations. It also shows the simple persistence baseline: tomorrow's station temperature stays the same as today's.

This is an experimental student project, not an exact answer, official forecast, or weather warning. Weather predictions have unavoidable error. It does not learn from predictions people request.

## Run it locally

```bash
python -m pip install -r requirements.txt
python app.py
```

## Model and evaluation

The HistGradientBoosting residual model was trained on 16,463 NOAA station examples from 2022–2023. Model selection used three chronological folds within those years. The fixed January–February 2024 validation MAEs (model vs persistence) were Karachi **1.031 vs 1.397 °C**, Lahore **1.082 vs 1.131 °C**, and Multan **1.226 vs 1.355 °C**. This is an early validation period, not proof of exact or future predictions.

The frozen model was scored once on two later partitions. On the 2024 locked test, MAE (model vs persistence) was Karachi **0.932 vs 0.892 °C**, Lahore **1.488 vs 1.923 °C**, and Multan **1.469 vs 1.896 °C**. On the separate 2025 reserve, it was Karachi **0.946 vs 1.033 °C**, Lahore **1.433 vs 1.857 °C**, and Multan **1.465 vs 1.866 °C**. Karachi's 2025 improvement uncertainty includes no improvement, and Karachi was slightly worse on the locked 2024 test. Do not describe it as a reliable win for Karachi. Lahore and Multan improved in both later evaluations, but estimates are still uncertain.

The approximate city-specific error bands use absolute errors from chronological training-only predictions. Their coverage is not guaranteed. Model estimates are never guaranteed to be exact.

## Data and limitations

- The target is the selected NOAA airport station's temperature 24 hours after the observed temperature. Live METAR airport readings are close to the training stations, but not necessarily identical sensors or exposures.
- Training temperatures were rounded to whole degrees to match METAR precision.
- JMA previous-day forecast fields come from Open-Meteo's [Previous Model Runs API](https://open-meteo.com/en/docs/previous-runs-api). Its `previous_day1` data represents a forecast made 24 hours before the valid time.
- Current METAR readings come from the [Aviation Weather Center Data API](https://aviationweather.gov/data/api/).
- A live-input availability check on 20 October 2026 retrieved a recent on-the-hour METAR and all ten JMA fields for the next-day target hour in each city. This verifies input availability at that moment; it does not verify prediction accuracy.
- The locked test and 2025 reserve were scored after freezing the model. Do not tune on those partitions.
- If either weather service is unavailable or required fields are missing, the app reports that the estimate is unavailable.

## Reproducibility

The app loads `karachi_station_jma_temperature_model.joblib` (a pooled three-city model). The training script, row-level validation predictions, training-only error bands, external diagnostic, and frozen evaluations are under `HeatShift_Training/experimental_data/station_jma_candidate/` in the repository.

Weather data credit: Open-Meteo.com, CC BY 4.0. [Open-Meteo terms](https://open-meteo.com/en/terms).

