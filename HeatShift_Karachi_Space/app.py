"""Gradio demo for HeatShift's experimental three-city temperature estimates."""
from __future__ import annotations

import json
import math
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

import gradio as gr
import joblib
import pandas as pd


ROOT = Path(__file__).resolve().parent
MODEL_FILE = ROOT / "karachi_station_jma_temperature_model.joblib"
TIME_ZONE = "Asia/Karachi"
TZ = ZoneInfo(TIME_ZONE)
UTC = ZoneInfo("UTC")
METAR_API = "https://aviationweather.gov/api/data/metar"
JMA_API = "https://previous-runs-api.open-meteo.com/v1/forecast"
CITY_CONFIG = {
    "Karachi": {"icao": "OPKC", "station_id": "41780099999", "latitude": 25.0, "longitude": 67.25},
    "Lahore": {"icao": "OPLA", "station_id": "41640099999", "latitude": 31.5, "longitude": 74.25},
    "Multan": {"icao": "OPMT", "station_id": "41675099999", "latitude": 30.25, "longitude": 71.5},
}
JMA_FEATURES = [
    "temperature_2m_previous_day1", "relative_humidity_2m_previous_day1",
    "dew_point_2m_previous_day1", "apparent_temperature_previous_day1",
    "precipitation_previous_day1", "cloud_cover_previous_day1",
    "wind_speed_10m_previous_day1", "wind_direction_10m_previous_day1",
    "surface_pressure_previous_day1", "pressure_msl_previous_day1",
]

# Empirical 90th-percentile absolute errors from chronological training-only
# predictions. They are approximate and are not guaranteed prediction coverage.
Q90_ERROR_BANDS_C = {"Karachi": 2.066, "Lahore": 2.830, "Multan": 2.809}
HISTORICAL_SCORES = {
    "Karachi": {"locked": "0.932 vs 0.892", "reserve": "0.946 vs 1.033", "reserve_ci": "-0.005 to +0.170"},
    "Lahore": {"locked": "1.488 vs 1.923", "reserve": "1.433 vs 1.857", "reserve_ci": "+0.304 to +0.557"},
    "Multan": {"locked": "1.469 vs 1.896", "reserve": "1.465 vs 1.866", "reserve_ci": "+0.316 to +0.487"},
}

with MODEL_FILE.open("rb") as model_file:
    MODEL_BUNDLE = joblib.load(model_file)


def fetch_latest_station_observation(city: str) -> tuple[datetime, dict]:
    """Fetch a recent on-the-hour METAR for the selected airport."""
    if city not in CITY_CONFIG:
        raise ValueError(f"Unknown city: {city}")
    icao = CITY_CONFIG[city]["icao"]
    params = urlencode({"ids": icao, "format": "json", "hours": 8})
    request = Request(f"{METAR_API}?{params}", headers={"User-Agent": "HeatShift-Temperature-Demo/1.0"})
    with urlopen(request, timeout=25) as response:
        reports = json.loads(response.read().decode("utf-8"))
    now = datetime.now(UTC)
    candidates = []
    for report in reports if isinstance(reports, list) else []:
        try:
            observed_at = datetime.fromtimestamp(int(report["obsTime"]), UTC)
            temp_c = float(report["temp"])
        except (KeyError, TypeError, ValueError, OverflowError):
            continue
        report_icao = report.get("icaoId")
        age = now - observed_at
        if (report_icao in (None, icao) and observed_at.minute == 0
                and timedelta(0) <= age <= timedelta(hours=4)):
            candidates.append((observed_at, report, temp_c))
    if not candidates:
        raise ValueError(f"No recent on-the-hour {icao} station temperature was returned.")
    observed_at, report, temp_c = max(candidates, key=lambda item: item[0])
    return observed_at, {**report, "temp_c": temp_c}


def fetch_jma_previous_day1(city: str, target_time: datetime) -> dict[str, float | None]:
    """Fetch JMA GSM inputs for the target hour from the matching city grid."""
    if city not in CITY_CONFIG:
        raise ValueError(f"Unknown city: {city}")
    config = CITY_CONFIG[city]
    params = urlencode({
        "latitude": config["latitude"],
        "longitude": config["longitude"],
        "models": "jma_gsm",
        "hourly": ",".join(JMA_FEATURES),
        "start_date": target_time.date().isoformat(),
        "end_date": target_time.date().isoformat(),
        "timezone": "UTC",
        "temperature_unit": "celsius",
    })
    request = Request(f"{JMA_API}?{params}", headers={"User-Agent": "HeatShift-Temperature-Demo/1.0"})
    with urlopen(request, timeout=30) as response:
        payload = json.loads(response.read().decode("utf-8"))
    if payload.get("error"):
        raise ValueError(payload.get("reason", "JMA forecast service returned an error."))
    hourly = payload.get("hourly", {})
    target_label = target_time.strftime("%Y-%m-%dT%H:%M")
    times = hourly.get("time", [])
    if target_label not in times:
        raise ValueError(f"JMA GSM did not return the target hour for {city}.")
    index = times.index(target_label)
    return {name: values[index] for name, values in hourly.items() if name != "time"}


def make_prediction(city: str = "Karachi") -> str:
    """Predict selected city's same-station temperature 24 hours ahead."""
    try:
        if city not in CITY_CONFIG:
            raise ValueError("Choose Karachi, Lahore, or Multan.")
        config = CITY_CONFIG[city]
        prediction_time, station_report = fetch_latest_station_observation(city)
        target_time = prediction_time + timedelta(hours=24)
        forecast = fetch_jma_previous_day1(city, target_time)
        current_temp = station_report["temp_c"]
        local_time = prediction_time.astimezone(TZ)
        hour = local_time.hour
        day_of_year = local_time.timetuple().tm_yday
        row_values = {
            "station_temp_input_c": round(current_temp),
            "hour_sin": math.sin(2 * math.pi * hour / 24.0),
            "hour_cos": math.cos(2 * math.pi * hour / 24.0),
            "year_sin": math.sin(2 * math.pi * (day_of_year - 1) / 365.2425),
            "year_cos": math.cos(2 * math.pi * (day_of_year - 1) / 365.2425),
            "station_id": config["station_id"],
            "hour_pk": str(hour),
            "month_pk": str(local_time.month),
        }
        row_values.update(forecast)
        available_fields = sum(forecast.get(name) is not None for name in JMA_FEATURES)
        if forecast.get("temperature_2m_previous_day1") is None or available_fields < 8:
            raise ValueError(f"Only {available_fields}/10 archived JMA forecast fields were available for {city}.")

        row = pd.DataFrame([row_values], columns=MODEL_BUNDLE["features"])
        prediction = float(MODEL_BUNDLE["pipeline"].predict(row)[0]) + current_temp
        band = Q90_ERROR_BANDS_C[city]
        target_local = target_time.astimezone(TZ)
        scores = HISTORICAL_SCORES[city]

        return (
            f"### {city}: temperature estimate for {target_local:%A, %d %B at %H:%M} PKT\n\n"
            f"- **HeatShift model estimate:** {prediction:.1f} °C\n"
            f"- **Persistence baseline:** {current_temp:.0f} °C (same as the current station reading)\n"
            f"- **Approximate historical 90% error band:** {prediction - band:.1f} to {prediction + band:.1f} °C\n"
            f"- **Input observation:** {local_time:%d %B %Y, %H:%M} PKT at {config['icao']} — "
            f"`{station_report.get('rawOb', 'METAR ' + config['icao'])}`\n"
            f"- **JMA previous-day forecast inputs available:** {available_fields}/10\n\n"
            f"**Past same-station scores (model MAE vs persistence MAE):** 2024 locked evaluation "
            f"{scores['locked']} °C; 2025 reserve evaluation {scores['reserve']} °C. "
            f"The 2025 paired improvement interval was {scores['reserve_ci']} °C.\n\n"
            "This is an experimental estimate, not an exact answer, official forecast, or weather warning. "
            "Forecast errors are unavoidable. The error band is based on training-only errors and is not a guarantee. "
            "The model uses the selected city's airport observation and its JMA grid forecast."
        )
    except Exception as exc:
        label = city if city in CITY_CONFIG else "selected city"
        return (
            f"### {label}: prediction unavailable\n\n"
            f"HeatShift could not retrieve a recent station reading and enough JMA inputs: "
            f"`{type(exc).__name__}: {exc}`. Try again later."
        )


demo = gr.Interface(
    fn=make_prediction,
    inputs=gr.Dropdown(choices=list(CITY_CONFIG), value="Karachi", label="Choose a city"),
    outputs=gr.Markdown(),
    title="HeatShift — 24-hour temperature estimate",
    description=(
        "Experimental same-station temperature estimates for Karachi, Lahore, and Multan. "
        "Each estimate is compared with the simple persistence baseline."
    ),
    submit_btn="Get temperature estimate",
    flagging_mode="never",
)


if __name__ == "__main__":
    demo.launch()

