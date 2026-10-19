"""Compare Ridge formulations for same-station temperature 24 hours ahead.

Uses train.csv for fitting and chronological tuning, and validation.csv for
model selection and reporting. Never opens test_locked.csv, replay.csv, or
reserve_2025.csv.
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
NUMERIC_FEATURES = ["temp_c", "temp_lag24_c", "temp_lag48_c", "lag24_missing", "lag48_missing"]
CATEGORICAL_FEATURES = ["station_id", "hour_pk", "month_pk"]
FEATURES = NUMERIC_FEATURES + CATEGORICAL_FEATURES
TARGET = "target_temp_24h_c"
BASELINE = "baseline_temp_24h_c"
ALPHAS = [0.01, 0.1, 1.0, 10.0, 100.0]


def load_partition(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path, dtype={"station_id": "string"})
    required = set(FEATURES + [TARGET, BASELINE, "city", "target_time_utc"])
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(f"{path.name} is missing required columns: {', '.join(missing)}")
    frame["target_time_utc"] = pd.to_datetime(frame["target_time_utc"], utc=True, errors="raise")
    for column in CATEGORICAL_FEATURES:
        frame[column] = frame[column].astype("string")
    for column in NUMERIC_FEATURES + [TARGET, BASELINE]:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    if frame[TARGET].isna().any() or frame[BASELINE].isna().any():
        raise ValueError(f"{path.name} contains rows without a measured target or baseline")
    return frame


def chronological_folds(train: pd.DataFrame):
    days = pd.DatetimeIndex(train["target_time_utc"].dt.floor("D").drop_duplicates().sort_values())
    if len(days) < 8:
        raise ValueError("Not enough distinct training dates for chronological folds")
    chunks = [chunk for chunk in np.array_split(days.to_numpy(), 4) if len(chunk)]
    folds = []
    for validation_days in chunks[1:]:
        start = pd.Timestamp(validation_days[0]).as_unit("ns")
        end = pd.Timestamp(validation_days[-1]).as_unit("ns") + pd.Timedelta(days=1)
        start = start.tz_localize("UTC") if start.tz is None else start.tz_convert("UTC")
        end = end.tz_localize("UTC") if end.tz is None else end.tz_convert("UTC")
        train_mask = train["target_time_utc"] < start - pd.Timedelta(hours=24)
        validation_mask = train["target_time_utc"].ge(start) & train["target_time_utc"].lt(end)
        if train_mask.any() and validation_mask.any():
            folds.append((train_mask, validation_mask, start.isoformat(), end.isoformat()))
    if len(folds) != 3:
        raise ValueError("Could not form three chronological folds from train.csv")
    return folds


def build_model(alpha: float, numeric_features=None) -> Pipeline:
    numeric_features = numeric_features or NUMERIC_FEATURES
    preparation = ColumnTransformer(transformers=[
        ("numeric", Pipeline([("fill_missing_lags", SimpleImputer(strategy="median")), ("scale", StandardScaler())]), numeric_features),
        ("categorical", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL_FEATURES),
    ])
    return Pipeline([("prepare_inputs", preparation), ("ridge_regression", Ridge(alpha=alpha))])


def tune(train, features, label, numeric_features, folds):
    results = []
    for alpha in ALPHAS:
        fold_rows = []
        for train_mask, val_mask, start, end in folds:
            model = build_model(alpha, numeric_features)
            model.fit(train.loc[train_mask, features], label.loc[train_mask])
            pred = model.predict(train.loc[val_mask, features])
            if label.name == "__temperature_change__":
                pred += train.loc[val_mask, "temp_c"].to_numpy()
            actual = train.loc[val_mask, TARGET]
            fold_rows.append({
                "validation_start_utc": start,
                "validation_end_utc": end,
                "training_examples": int(train_mask.sum()),
                "validation_examples": int(val_mask.sum()),
                "mae_c": float(mean_absolute_error(actual, pred)),
            })
        results.append({"alpha": alpha, "mean_fold_mae_c": float(np.mean([r["mae_c"] for r in fold_rows])), "folds": fold_rows})
    return min(results, key=lambda r: (r["mean_fold_mae_c"], r["alpha"])), results


def group_metrics(frame, actual, ridge_pred, baseline_pred, hot_threshold):
    hour = pd.to_numeric(frame["hour_pk"], errors="coerce")
    groups = {
        "city": frame["city"].astype("string"),
        "month_pk": frame["month_pk"].astype("string"),
        "pkt_time_block": pd.cut(hour, bins=[-1, 5, 11, 17, 23], labels=["night_00_05", "morning_06_11", "afternoon_12_17", "evening_18_23"]).astype("string"),
        "temperature_group": pd.Series(np.where(frame["temp_c"].to_numpy() >= hot_threshold, "hot_top_10pct_of_training", "other"), index=frame.index, dtype="string"),
    }
    rows = []
    for kind, values in groups.items():
        for value in values.dropna().unique():
            positions = np.flatnonzero(values.eq(value).to_numpy())
            a, rp, bp = actual[positions], ridge_pred[positions], baseline_pred[positions]
            rows.append({"group_type": kind, "group_value": str(value), "examples": int(len(positions)),
                         "ridge_mae_c": float(mean_absolute_error(a, rp)), "baseline_mae_c": float(mean_absolute_error(a, bp)),
                         "ridge_rmse_c": float(np.sqrt(mean_squared_error(a, rp))), "baseline_rmse_c": float(np.sqrt(mean_squared_error(a, bp)))})
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=ROOT / "02_final")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "model_results")
    args = parser.parse_args()
    train = load_partition(args.data_dir / "train.csv")
    validation = load_partition(args.data_dir / "validation.csv")
    folds = chronological_folds(train)
    candidates, models, predictions = [], {}, {}

    for mode in ["direct_temperature", "temperature_change"]:
        label = train[TARGET] if mode == "direct_temperature" else (train[TARGET] - train["temp_c"]).rename("__temperature_change__")
        selected, tuning = tune(train, FEATURES, label, NUMERIC_FEATURES, folds)
        model = build_model(float(selected["alpha"]))
        model.fit(train[FEATURES], label)
        pred = model.predict(validation[FEATURES])
        if mode == "temperature_change":
            pred += validation["temp_c"].to_numpy()
        candidate_id = f"{mode}_all_features"
        models[candidate_id], predictions[candidate_id] = model, pred
        candidates.append({"candidate_id": candidate_id, "prediction_mode": mode, "feature_set": "all_contract_features",
                           "selected_alpha": float(selected["alpha"]), "training_cv": tuning,
                           "validation_mae_c": float(mean_absolute_error(validation[TARGET], pred))})

    no48_numeric = [name for name in NUMERIC_FEATURES if name not in {"temp_lag48_c", "lag48_missing"}]
    no48_features = no48_numeric + CATEGORICAL_FEATURES
    change_label = (train[TARGET] - train["temp_c"]).rename("__temperature_change__")
    selected, tuning = tune(train, no48_features, change_label, no48_numeric, folds)
    model = build_model(float(selected["alpha"]), no48_numeric)
    model.fit(train[no48_features], change_label)
    pred = model.predict(validation[no48_features]) + validation["temp_c"].to_numpy()
    no48_id = "temperature_change_without_48h_lag"
    models[no48_id], predictions[no48_id] = model, pred
    candidates.append({"candidate_id": no48_id, "prediction_mode": "temperature_change",
                       "feature_set": "all_contract_features_except_temp_lag48_and_marker",
                       "selected_alpha": float(selected["alpha"]), "training_cv": tuning,
                       "validation_mae_c": float(mean_absolute_error(validation[TARGET], pred))})

    winner = min(candidates, key=lambda row: row["validation_mae_c"])
    selected_id, mode = winner["candidate_id"], winner["prediction_mode"]
    model, pred = models[selected_id], predictions[selected_id]
    features = no48_features if selected_id == no48_id else FEATURES
    actual, baseline = validation[TARGET].to_numpy(), validation[BASELINE].to_numpy()
    ridge_mae = float(mean_absolute_error(actual, pred))
    baseline_mae = float(mean_absolute_error(actual, baseline))
    improvement = baseline_mae - ridge_mae
    hot_threshold = float(train["temp_c"].quantile(.9))
    groups = group_metrics(validation, actual, pred, baseline, hot_threshold)
    by_city = {r["group_value"]: {"examples": r["examples"], "ridge_mae_c": r["ridge_mae_c"], "baseline_mae_c": r["baseline_mae_c"]} for r in groups if r["group_type"] == "city"}
    args.output_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump({"pipeline": model, "prediction_mode": mode, "features": features}, args.output_dir / "ridge_temperature_model.joblib")
    cols = [c for c in ["example_id", "city", "station_id", "prediction_time_utc", "target_time_utc"] if c in validation.columns]
    table = validation[cols].copy()
    table["actual_temp_24h_c"], table["ridge_prediction_c"], table["baseline_prediction_c"] = actual, pred, baseline
    table["ridge_absolute_error_c"], table["baseline_absolute_error_c"] = np.abs(actual-pred), np.abs(actual-baseline)
    table.to_csv(args.output_dir / "validation_predictions.csv", index=False)
    pd.DataFrame(groups).to_csv(args.output_dir / "validation_group_metrics.csv", index=False)
    report = {
        "model": "Ridge regression", "ridge_alpha": float(winner["selected_alpha"]), "prediction_mode": mode,
        "selected_candidate_id": selected_id, "target": "same-station measured temperature 24 hours later (C)",
        "training_examples": int(len(train)), "validation_examples": int(len(validation)),
        "training_period": "2023 only in the supplied files; NOAA 2022 files are absent",
        "validation_period": "2024-01-01 through 2024-02-29, by target UTC time",
        "ridge": {"mae_c": ridge_mae, "rmse_c": float(np.sqrt(mean_squared_error(actual, pred)))},
        "baseline": {"mae_c": baseline_mae, "rmse_c": float(np.sqrt(mean_squared_error(actual, baseline)))},
        "ridge_candidates_compared_on_validation": candidates,
        "selected_alpha_by_training_folds": float(winner["selected_alpha"]),
        "hot_subset_definition": {"rule": "current temperature at or above training-set 90th percentile", "training_threshold_c": hot_threshold},
        "mae_improvement_c": float(improvement),
        "mae_improvement_percent": float(100*improvement/baseline_mae) if baseline_mae else None,
        "ridge_beats_baseline_on_validation": bool(improvement > 0), "by_city": by_city,
        "notes": ["The baseline predicts that the temperature 24 hours later equals the current temperature.",
                  "Ridge alpha was selected using three chronological folds inside training data only.",
                  "Direct-temperature and temperature-change Ridge formulations were compared on validation.",
                  "Ridge is compared with the baseline on exactly the same validation rows.",
                  "Validation is for checking choices; it is not the final locked test.",
                  "Validation errors are also grouped by city, month, PKT time block, and a training-defined hot subset.",
                  "No test_locked, replay, or reserve_2025 rows were read by this script."],
    }
    (args.output_dir / "validation_metrics.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
