"""Small Gradio demo for HeatShift's Karachi temperature estimate."""
from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

import gradio as gr
import joblib
import pandas as pd


ROOT = Path(__file__).resolve().parent
MODEL_FILE = ROOT / "ridge_temperature_model.joblib"
TIME_ZONE = "Asia/Karachi"
TZ = ZoneInfo(TIME_ZONE)
LATITUDE = 25.0
LONGITUDE = 67.25
CITY = "Karachi"
STATION_ID = "41780099999"

with MODEL_FILE.open("rb") as model_file:
    MODEL_BUNDLE = joblib.load(model_file)


def fetch_hourly_temperatures() -> dict[datetime, float]:
    """Get recent hourly city-grid temperatures from Open-Meteo."""
    params = urlencode({
        "latitude": LATITUDE,
        "longitude": LONGITUDE,
        "hourly": "temperature_2m",
        "past_days": 2,
        "forecast_days": 2,
        "timezone": TIME_ZONE,
        "temperature_unit": "celsius",
    })
    request = Request(
        f"https://api.open-meteo.com/v1/forecast?{params}",
        headers={"User-Agent": "HeatShift-Karachi-Demo/1.0"},
    )
    with urlopen(request, timeout=20) as response:
        data = json.loads(response.read().decode("utf-8"))

    times = data.get("hourly", {}).get("time", [])
    values = data.get("hourly", {}).get("temperature_2m", [])
    if not times or len(times) != len(values):
        raise ValueError("The weather provider returned no hourly temperatures.")

    result = {}
    for time_text, value in zip(times, values):
        if value is None:
            continue
        local_time = datetime.fromisoformat(time_text).replace(tzinfo=TZ)
        result[local_time] = float(value)
    return result


def make_prediction() -> str:
    """Predict Karachi's next-day same-hour temperature and show baseline."""
    try:
        hourly = fetch_hourly_temperatures()
        now = datetime.now(TZ)
        prediction_time = now.replace(minute=0, second=0, microsecond=0)

        # Use the latest completed hourly point if this hour has not arrived yet.
        while prediction_time not in hourly and prediction_time > now - timedelta(hours=3):
            prediction_time -= timedelta(hours=1)
        if prediction_time not in hourly:
            raise ValueError("No recent hourly temperature was available for Karachi.")

        current_temp = hourly[prediction_time]
        lag24 = hourly.get(prediction_time - timedelta(hours=24))
        lag48 = hourly.get(prediction_time - timedelta(hours=48))
        hour_pk = str(prediction_time.hour)
        month_pk = str(prediction_time.month)
        row = pd.DataFrame([{
            "temp_c": current_temp,
            "temp_lag24_c": lag24,
            "temp_lag48_c": lag48,
            "lag24_missing": int(lag24 is None),
            "lag48_missing": int(lag48 is None),
            "station_id": STATION_ID,
            "hour_pk": hour_pk,
            "month_pk": month_pk,
        }], columns=MODEL_BUNDLE["features"])

        model_value = float(MODEL_BUNDLE["pipeline"].predict(row)[0])
        if MODEL_BUNDLE["prediction_mode"] == "temperature_change":
            model_value += current_temp

        target_time = prediction_time + timedelta(hours=24)
        return (
            f"### Karachi: temperature estimate for {target_time:%A, %d %B at %H:%M} PKT\n\n"
            f"- **HeatShift Ridge estimate:** {model_value:.1f} °C\n"
            f"- **Simple baseline (same as today):** {current_temp:.1f} °C\n"
            f"- **Input time:** {prediction_time:%d %B %Y, %H:%M} PKT\n"
            f"- **Recent temperatures used:** 24-hour lag {lag24 if lag24 is not None else 'missing'}; "
            f"48-hour lag {lag48 if lag48 is not None else 'missing'} °C\n\n"
            "**Please read:** this is a prototype estimate, not an official forecast. Its live inputs are "
            "Open-Meteo grid-model temperatures near Karachi, while the model was trained on NOAA station "
            "measurements. That live-input combination has not been validated, and Ridge did not beat the "
            "baseline in the project's validation."
        )
    except Exception as exc:
        return (
            "### Prediction unavailable\n\n"
            f"HeatShift could not retrieve the current Karachi weather input: `{type(exc).__name__}: {exc}`. "
            "Try again when the weather service is reachable."
        )


demo = gr.Interface(
    fn=make_prediction,
    inputs=[],
    outputs=gr.Markdown(),
    title="HeatShift — Karachi 24-hour temperature demo",
    description=(
        "Press the button to compare the experimental Ridge estimate with the simple "
        "'same temperature tomorrow' baseline."
    ),
    submit_btn="Get Karachi estimate",
    allow_flagging="never",
)


if __name__ == "__main__":
    demo.launch()

