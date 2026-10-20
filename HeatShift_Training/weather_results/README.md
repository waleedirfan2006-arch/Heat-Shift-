# Station-weather model

## What it uses
The same current station record's temperature, dew point and wind, plus station and known PKT calendar features. Training sources are the warehouse files uploaded by Amaan. No new weather dataset was downloaded. Mateen's files were not accessed or modified in this update.

Dew point and wind are decoded from the selected current raw record, using its clean-table record reference. Quality codes 0, 1, 4 and 5 are accepted. NOAA documents temperature/dew point in tenths of Celsius and wind speed in tenths of metres per second. Dew point is kept in the documented −98.2 to 36.8 C domain; wind in 0–90 m/s. Both the fitted residual reference and browser output use whole-degree current temperature. Model inputs use whole-degree temperature/dew point and integer wind knots to match METAR report precision. Calm/variable direction remains missing. Source: https://www.ncei.noaa.gov/pub/data/noaa/isd-format-document.pdf, mandatory section, pages 8–11.

## Selection and measured results
Four Ridge, eight HGB and two ExtraTrees settings were compared at four fixed residual weights on three expanding training folds: 56 comparisons. After matching METAR input precision, HGB had the lowest training-CV MAE across all compared estimator families. That same winner is compatible with the existing browser engine and was fitted and exported. It was not selected by validation score.

The browser model uses absolute-error HGB, 200 iterations, 15 leaves, and residual weight 0.75. It was fitted on all 16,463 training rows. Fixed development validation has 1,783 rows:

| Measure | New weather model | Same-row baseline |
|---|---:|---:|
| MAE (C) | 1.228046 | 1.235165 |
| RMSE (C) | 1.609206 | 1.664814 |

For context, whole-degree persistence MAE is 1.243915 C; the original fixed raw-reading baseline remains the main benchmark. The mean MAE difference is small: 0.007119 C. A 7-day-block bootstrap interval is −0.074115 to 0.078479 C, including no improvement. Lahore's model MAE is slightly worse than its baseline. Do not claim statistically established superiority or a win. Validation was reused during development, so it is not a fresh independent final evaluation. No locked-test, replay or reserve rows were scored or used for selection.

The original JMA model remains the dashboard default. Its archived training features were not uploaded, so it cannot be fairly rescored head-to-head here. The new model is a reproducible option when JMA requests fail; it still needs a real, recent station report.

## Files
- browser_weather_model.joblib: fitted portable-model pipeline and selected weight.
- browser_weather_model.json.gz: compressed browser export.
- browser_model_metrics.json: measured results, city errors, interval and fingerprints.
- browser_validation_predictions.csv: the 1,783 actual validation predictions.
- browser_parity_vectors.json.gz: real-feature software parity checks; not extra training data.
- metrics.json: full candidate search, including non-deployed estimator families.
- validation_predictions.csv: research winner's validation results.

The large research winner's joblib file is rebuilt by the script rather than committed. The browser HGB artifact is included. The new model’s displayed ranges now use a separate March 2024 calibration split with per-city finite-sample quantiles. Time dependence prevents a guarantee of future coverage. Training-fold ranges remain archived for comparison.

## Reproduce
Use Python 3.12 with the included requirements.txt. From the repository root:

    python HeatShift_Training/train_weather_model.py
    python HeatShift_Training/finalize_browser_weather_model.py
    python HeatShift_Training/calibrate_weather_model.py
    python HeatShift_Training/verify_browser_weather_inputs.py
    node HeatShift_Static_Space/check_weather_parity.js HeatShift_Training/weather_results/browser_parity_vectors.json.gz

Training, feature extraction and preprocessing use training data only during folds. The validation file is only scored afterward. Input and raw-source hashes are recorded. Original event arrival/revision times are unverified, and historical NOAA scoring does not independently establish live METAR performance.

The full input-construction check matches 1,771 real reports with usable dew point and wind. Twelve validation rows without dew point cannot be entered in the station-weather form; model-engine parity still covers all 1,783 rows. Wind angle conversion follows the same arithmetic order as NumPy.
