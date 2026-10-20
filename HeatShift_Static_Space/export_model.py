"""Export the frozen sklearn pipeline as compact JSON for static JS inference."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import joblib


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "HeatShift_Karachi_Space" / "karachi_station_jma_temperature_model.joblib"
OUTPUT = Path(__file__).resolve().parent / "model.json"


def main() -> None:
    bundle = joblib.load(SOURCE)
    pipeline = bundle["pipeline"]
    prep = pipeline.named_steps["prepare"]
    estimator = pipeline.named_steps["regressor"]
    numeric = prep.transformers_[0][1]
    encoder = prep.transformers_[1][1]

    trees = []
    for iteration in estimator._predictors:
        for predictor in iteration:
            nodes = []
            for node in predictor.nodes:
                nodes.append({
                    "value": float(node["value"]),
                    "feature": int(node["feature_idx"]),
                    "bin": int(node["bin_threshold"]),
                    "left": int(node["left"]),
                    "right": int(node["right"]),
                    "leaf": bool(node["is_leaf"]),
                })
            trees.append(nodes)

    model = {
        "format": "heatshift-hgb-js-v1",
        "selected_candidate": bundle.get("selected_candidate", "frozen"),
        "source_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        "features": bundle["features"],
        "numeric_features": prep.transformers_[0][2],
        "medians": numeric.named_steps["impute"].statistics_.tolist(),
        "means": numeric.named_steps["scale"].mean_.tolist(),
        "scales": numeric.named_steps["scale"].scale_.tolist(),
        "categorical_features": prep.transformers_[1][2],
        "categories": [array.astype(str).tolist() for array in encoder.categories_],
        "bin_thresholds": [array.tolist() for array in estimator._bin_mapper.bin_thresholds_],
        "baseline": float(estimator._baseline_prediction.ravel()[0]),
        "trees": trees,
    }
    OUTPUT.write_text(json.dumps(model, separators=(",", ":")) + "\n", encoding="utf-8")
    print(f"Wrote {OUTPUT} ({OUTPUT.stat().st_size:,} bytes, {len(trees)} trees).")


if __name__ == "__main__":
    main()

