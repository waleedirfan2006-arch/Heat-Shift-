---
title: HeatShift Karachi Demo
emoji: 🌤️
colorFrom: blue
colorTo: orange
sdk: gradio
python_version: 3.10
app_file: app.py
pinned: false
---

# HeatShift Karachi 24-hour temperature demo

This beginner prototype uses a saved Ridge regression model to estimate Karachi's temperature at the same hour tomorrow. It also shows the simple baseline: tomorrow's temperature equals today's.

## Run it locally

From this folder:

```bash
python -m pip install -r requirements.txt
python app.py
```

## How the demo works

The app gets hourly 2-metre temperature values from the Open-Meteo Forecast API for the project's existing Karachi grid point (25.00, 67.25). It supplies the latest hourly value and the values 24 and 48 hours earlier to the saved Ridge model, then predicts for the same hour on the following day.

The model was trained on NOAA station observations, while this demo uses Open-Meteo grid-model inputs. The combination has not been validated. Validation MAE for the trained Ridge model was 1.321 °C compared with 1.235 °C for the baseline. Treat both displayed values as a classroom demonstration, not reliable weather advice; the baseline performed better in the project evaluation.

Weather data credit: Open-Meteo.com, CC BY 4.0. [Open-Meteo terms](https://open-meteo.com/en/terms).

The app needs an internet connection to retrieve current weather. It does not update model weights from predictions. To publish it, create a public Gradio Space and upload the files in this folder. Hugging Face reads the Space settings from the YAML block at the top of this README and installs packages listed in `requirements.txt`.

