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

Do not use the locked test data to tune the model. Keep it untouched until the model and choices are finalized.

