# New station-only training experiment

This trained challenger uses the observed station temperature and calendar only. It needs no archived weather download. It was selected using training-only folds and scored on the fixed validation period afterward. Its validation MAE was slightly worse than persistence, so it is not the production predictor.

Files:
- metrics.json: candidates, folds, measured errors, source fingerprints and limits.
- validation_predictions.csv: one prediction per validation example for checking the recorded errors.
- station_challenger.joblib: fitted selected model. Load with the pinned sklearn version and only from this trusted project source.
- fallback.json: conservative persistence fallback, not the trained HGB.
- requirements.txt: exact experiment environment versions.

Run from the repository root:

    python HeatShift_Training/optimize_station_model.py

The script writes these results. It does not open test_locked.csv, replay.csv or reserve_2025.csv.
