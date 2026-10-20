# HeatShift

HeatShift is a beginner weather project that predicts the temperature at the same weather station 24 hours later. This prototype uses historical observations from three stations in Pakistan; it is not yet a live forecast for every location.

## First regression model

The project uses Ridge regression and compares it with a simple baseline: predict that tomorrow's temperature will be the same as today's. The script checks settings using time-ordered folds from the training data, then compares model choices on the separate validation data.

### Validation results

| Approach | Mean absolute error |
|---|---:|
| Simple baseline: tomorrow equals today | 1.235 °C |
| Ridge, direct temperature prediction | 1.382 °C |
| Ridge, predict temperature change | 1.321 °C |
| Ridge, temperature change without the 48-hour lag | 1.326 °C |

Lower error is better. The best Ridge version is the temperature-change model, but its validation error is still higher than the baseline's. The model has **not beaten the baseline**, so this project does not claim that it has. The locked test data has not been used; keep it untouched until the model and choices are finalized.

The detailed results are in [`HeatShift_Training/model_results/validation_metrics.json`](HeatShift_Training/model_results/validation_metrics.json). They include error breakdowns and details of the candidate comparisons.

## Run the model

Open a terminal in `HeatShift_Training`, then run:

```bash
python -m pip install -r requirements.txt
python train_model.py
```

The script reads `HeatShift_Warehouse/02_final/train.csv` and `validation.csv`. It saves the fitted model, validation scores, and example predictions in `HeatShift_Training/model_results/`. It does not read `test_locked.csv`, `replay.csv`, or `reserve_2025.csv`.

The data files and their cleaning notes are in [`HeatShift_Warehouse/START_HERE.md`](HeatShift_Warehouse/START_HERE.md).


## Data audit update

See [HeatShift_Warehouse/audit/DATA_QUALITY_AND_LEAKAGE_REVIEW.md](HeatShift_Warehouse/audit/DATA_QUALITY_AND_LEAKAGE_REVIEW.md) and [HeatShift_Warehouse/audit/OPEN_METEO_PROVENANCE.md](HeatShift_Warehouse/audit/OPEN_METEO_PROVENANCE.md). Structural audit completed with limitations. Original Open-Meteo collection evidence remains incomplete. Earlier model results have not been rerun on the expanded data.
