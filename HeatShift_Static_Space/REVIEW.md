# Model and website update — 21 October 2026 PKT

## Result
The website now supports city selection, raw METAR parsing, Celsius/Fahrenheit display, dark mode, explicit baseline mode, session comparison history, prediction downloads, and a model-evidence page. It retains Waleed's frozen JMA/HGB predictor. Agent files were not changed.

## Model work actually performed
- Used GitHub's uploaded train.csv (16,463 rows) and validation.csv (1,783 rows).
- Applied the existing data guards before training.
- Trained four Ridge and four HistGradientBoosting candidate configurations, plus a persistence reference.
- Selected the lowest pooled MAE across three chronological expanding training folds. Training labels finish before each fold's prediction times.
- Selected HGB: 250 iterations, 7 leaves, absolute-error loss. Final model fitted on all training rows and saved in HeatShift_Training/station_results/station_challenger.joblib.
- Training-fold MAE: 1.356226 C; same-row baseline 1.374255 C.
- Fixed validation MAE: 1.237479 C; same-row baseline 1.235165 C.
- Validation RMSE: 1.621536 C. The challenger did not establish a validation MAE improvement, so it is not promoted.
- This is a new station-only experiment. It is not a recreation of Waleed's JMA feature-training run. Do not compare its validation score against a different row subset in the JMA model card.
- Validation has been examined previously; these results are not a new independent final test. No locked-test, replay or 2025 reserve files were read by the experiment.

## Repairs to the current model deployment
The original JavaScript converted null weather values into zero. It now applies the saved training median, matching Python. Empty temperatures no longer become zero. Inputs must be whole-degree station temperatures at an exact hour in the last four hours. The default input is blank to avoid suggesting an invented observation.

The exported frozen model content is semantically identical to the original live Space model. Python and browser inference matched on 51 constructed test cases, including missing numeric values (maximum difference zero). Constructed fixtures were only software tests, never model training or evaluation data.

## Website limits
The target is airport temperature exactly 24 hours after the observed report, not rain or a complete weather forecast. A manually pasted report is not authenticated by the page. Weather API requests time out after 20 seconds. Service failure produces a visible error; baseline-only mode must be selected explicitly. Historical error bands are not guaranteed coverage intervals.

The original JMA model card's accuracy numbers remain publisher-reported here: the archived JMA training features, fitting script and per-row scoring evidence were not found in the inspected main and remote history. Its own card reports Karachi's 2024 test result worse than persistence. Existing test/reserve outcomes must not guide further model selection.

## Reproduce
Use Python 3.12 and HeatShift_Training/station_results/requirements.txt.

    python HeatShift_Training/optimize_station_model.py
    node HeatShift_Static_Space/test_browser_form.js
    python HeatShift_Static_Space/verify_model_parity.py

The optimizer does not fetch weather data. It uses the GitHub warehouse inputs and records their SHA256 fingerprints. Results include candidate/fold scores, city metrics, validation predictions, runtime and the saved challenger. The model export/parity script uses the frozen original JMA joblib file with scikit-learn 1.6.1.

## Deployment
Static Space deployment needs index.html, style.css, app.js, core.js, model.js, model.json, experiment.json, REVIEW.md and README.md at the Space root. The repository provides this folder; GitHub and Hugging Face are separate deployments. Do not assume a GitHub merge updates Hugging Face unless a sync is configured. This model/website update does not resolve the guide's separate Gradio/Streamlit requirement.
