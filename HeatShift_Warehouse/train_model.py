"""Train and evaluate HeatShift's first 24-hour temperature model.

Run from this folder with: python train_model.py
The script learns from train.csv and reports scores on validation.csv only.
It does not read test_locked.csv, replay.csv, or reserve_2025.csv.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


ROOT = Path(__file__).resolve().parent
NUMERIC_FEATURES = [
    "temp_c",
    "temp_lag24_c",
    "temp_lag48_c",
    "lag24_missing",
    "lag48_missing",
]
CATEGORICAL_FEATURES = ["station_id", "hour_pk", "month_pk"]
FEATURES = NUMERIC_FEATURES + CATEGORICAL_FEATURES
TARGET = "target_temp_24h_c"
BASELINE = "baseline_temp_24h_c"


def load_partition(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path, dtype={"station_id": "string"})
    required = set(FEATURES + [TARGET, BASELINE, "city"])
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(f"{path.name} is missing required columns: {', '.join(missing)}")

    # Treat the clock fields as categories, not continuous numbers.
    for column in CATEGORICAL_FEATURES:
        frame[column] = frame[column].astype("string")
    for column in NUMERIC_FEATURES + [TARGET, BASELINE]:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")

    # A labelled example and the fixed baseline both require a measured
    # current and future temperature. Never invent either value.
    usable = frame[TARGET].notna() & frame[BASELINE].notna()
    if not usable.all():
        raise ValueError(f"{path.name} contains rows without a measured target or baseline.")
    return frame


def scores(actual: pd.Series, predicted: np.ndarray) -> dict[str, float]:
    return {
        "mae_c": float(mean_absolute_error(actual, predicted)),
        "rmse_c": float(np.sqrt(mean_squared_error(actual, predicted))),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=ROOT / "02_final",
        help="Folder containing train.csv and validation.csv.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ROOT / "model_results",
        help="Folder for the saved model and validation results.",
    )
    args = parser.parse_args()

    train = load_partition(args.data_dir / "train.csv")
    validation = load_partition(args.data_dir / "validation.csv")

    numeric_steps = Pipeline(
        steps=[
            ("fill_missing_lags", SimpleImputer(strategy="median")),
            ("scale", StandardScaler()),
        ]
    )
    categorical_steps = OneHotEncoder(handle_unknown="ignore")
    preparation = ColumnTransformer(
        transformers=[
            ("numeric", numeric_steps, NUMERIC_FEATURES),
            ("categorical", categorical_steps, CATEGORICAL_FEATURES),
        ]
    )
    model = Pipeline(
        steps=[
            ("prepare_inputs", preparation),
            ("ridge_regression", Ridge(alpha=1.0)),
        ]
    )

    # The whole pipeline is fitted on train.csv, so missing-value replacements,
    # scaling, and category handling are learned from training rows only.
    model.fit(train[FEATURES], train[TARGET])
    predictions = model.predict(validation[FEATURES])
    actual = validation[TARGET].to_numpy()
    baseline_predictions = validation[BASELINE].to_numpy()

    model_scores = scores(validation[TARGET], predictions)
    baseline_scores = scores(validation[TARGET], baseline_predictions)
    improvement = baseline_scores["mae_c"] - model_scores["mae_c"]
    improvement_pct = (
        100 * improvement / baseline_scores["mae_c"]
        if baseline_scores["mae_c"] > 0
        else None
    )

    by_city = {}
    for city, group in validation.groupby("city", sort=True):
        mask = validation["city"].eq(city).to_numpy()
        by_city[str(city)] = {
            "examples": int(len(group)),
            "ridge": scores(group[TARGET], predictions[mask]),
            "baseline": scores(group[TARGET], baseline_predictions[mask]),
        }

    args.output_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, args.output_dir / "ridge_temperature_model.joblib")

    prediction_columns = [
        column
        for column in ["example_id", "city", "station_id", "prediction_time_utc", "target_time_utc"]
        if column in validation.columns
    ]
    prediction_table = validation[prediction_columns].copy()
    prediction_table["actual_temp_24h_c"] = actual
    prediction_table["ridge_prediction_c"] = predictions
    prediction_table["baseline_prediction_c"] = baseline_predictions
    prediction_table["ridge_absolute_error_c"] = np.abs(actual - predictions)
    prediction_table["baseline_absolute_error_c"] = np.abs(actual - baseline_predictions)
    prediction_table.to_csv(args.output_dir / "validation_predictions.csv", index=False)

    report = {
        "model": "Ridge regression",
        "ridge_alpha": 1.0,
        "target": "same-station measured temperature 24 hours later (C)",
        "training_examples": int(len(train)),
        "validation_examples": int(len(validation)),
        "training_period": "2023 only in the supplied files; NOAA 2022 files are absent",
        "validation_period": "2024-01-01 through 2024-02-29, by target UTC time",
        "ridge": model_scores,
        "baseline": baseline_scores,
        "mae_improvement_c": float(improvement),
        "mae_improvement_percent": float(improvement_pct) if improvement_pct is not None else None,
        "ridge_beats_baseline_on_validation": bool(improvement > 0),
        "by_city": by_city,
        "notes": [
            "The baseline predicts that the temperature 24 hours later equals the current temperature.",
            "Ridge is compared with the baseline on exactly the same validation rows.",
            "Validation is for checking choices; it is not the final locked test.",
            "No test_locked, replay, or reserve_2025 rows were read by this script.",
        ],
    }
    (args.output_dir / "validation_metrics.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )

    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
