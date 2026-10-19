# Train the HeatShift model

This folder contains the first temperature prediction model and its validation report. The data warehouse is kept separately in `HeatShift_Warehouse`.

## Run it

From this folder, install the packages and run the model:

```bash
python -m pip install -r requirements.txt
python train_model.py
```

The script learns from `HeatShift_Warehouse/02_final/train.csv` and checks choices on `HeatShift_Warehouse/02_final/validation.csv`. It never reads the locked test file, replay data, or the 2025 reserve data.

## Validation result

The best Ridge version predicts the temperature change. Its mean absolute error is **1.321 °C**; the simple baseline's error is **1.235 °C**. Lower is better, so Ridge has not beaten the baseline. See [`model_results/validation_metrics.json`](model_results/validation_metrics.json) for details.

We also checked Open-Meteo history and additional NOAA station weather fields as possible inputs, and whether to choose Ridge or the baseline separately for each city. The experiments and results are in [`optimization_log.md`](optimization_log.md). No tested version beat the baseline, so the model inputs and policy were not changed. NOAA station observations remain the training answers; Open-Meteo estimates were not used as station observations or to fill missing values.

We also evaluated archived Open-Meteo GFS forecasts made 24 hours before the target time. The raw GFS forecast performed worse than persistence, and a bias-corrected blend did not pass training-only chronological checks, so neither was adopted. The experiment had incomplete validation coverage; see [`optimization_log.md`](optimization_log.md) for the matched-row results.

Do not use the locked test data to tune the model. Keep it untouched until the model and choices are finalized.

