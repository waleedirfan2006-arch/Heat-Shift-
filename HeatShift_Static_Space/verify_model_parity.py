"""Compare exported browser inference with the frozen sklearn pipeline."""
from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from pathlib import Path

import joblib
import numpy as np
import pandas as pd


HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SOURCE = ROOT / "HeatShift_Karachi_Space" / "karachi_station_jma_temperature_model.joblib"


def main() -> None:
    bundle = joblib.load(SOURCE)
    rng = np.random.default_rng(20261020)
    cities = ["41780099999", "41640099999", "41675099999"]
    rows = []
    for i in range(36):
        hour = (i * 7) % 24
        day = (i * 31) % 365 + 1
        rows.append({
            "station_temp_input_c": float(rng.integers(4, 46)),
            "hour_sin": float(np.sin(2 * np.pi * hour / 24)),
            "hour_cos": float(np.cos(2 * np.pi * hour / 24)),
            "year_sin": float(np.sin(2 * np.pi * (day - 1) / 365.2425)),
            "year_cos": float(np.cos(2 * np.pi * (day - 1) / 365.2425)),
            "temperature_2m_previous_day1": float(rng.uniform(2, 48)),
            "relative_humidity_2m_previous_day1": float(rng.uniform(10, 100)),
            "dew_point_2m_previous_day1": float(rng.uniform(-10, 31)),
            "apparent_temperature_previous_day1": float(rng.uniform(1, 49)),
            "precipitation_previous_day1": float(rng.uniform(0, 20)),
            "cloud_cover_previous_day1": float(rng.uniform(0, 100)),
            "wind_speed_10m_previous_day1": float(rng.uniform(0, 50)),
            "wind_direction_10m_previous_day1": float(rng.uniform(0, 360)),
            "surface_pressure_previous_day1": float(rng.uniform(970, 1030)),
            "pressure_msl_previous_day1": float(rng.uniform(970, 1035)),
            "station_id": cities[i % 3],
            "hour_pk": str(hour),
            "month_pk": str(i % 12 + 1),
        })
    frame = pd.DataFrame(rows, columns=bundle["features"])
    expected = bundle["pipeline"].predict(frame)
    vectors = [{"row": row, "expected": float(value)} for row, value in zip(rows, expected)]
    node = shutil.which("node")
    if not node:
        raise RuntimeError("Node.js is required for this inference parity check.")
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".json", delete=False) as handle:
        json.dump(vectors, handle)
        path = Path(handle.name)
    try:
        subprocess.run([node, str(HERE / "check_model_parity.js"), str(path)], cwd=HERE, check=True)
    finally:
        path.unlink(missing_ok=True)


if __name__ == "__main__":
    main()

