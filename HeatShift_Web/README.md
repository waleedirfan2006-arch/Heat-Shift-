---
title: HeatShift Weather Dashboard
emoji: ☀️
colorFrom: green
colorTo: yellow
sdk: static
app_file: index.html
---

# HeatShift dashboard

Live app: https://huggingface.co/spaces/Waleed-1234/HeatShift-Dashboard

This static Space uses Waleed’s frozen airport-temperature model and runs Syed Mateen Ali’s original two Python agents in the visitor’s browser. Uploaded files remain in that browser. First use loads Python and pandas; allow up to two minutes in a new tab. Warm it up before presenting.

## Easy demo

Open **Data quality**. `karachi_training_sample.csv` is 5,012 real NOAA training observations and is already clean. To show decisions, use `HeatShift_QA_Practice_SAMPLE_SYNTHETIC.csv`, clearly labeled fabricated practice data: one duplicate, two short gaps, a four-row gap, and an out-of-range value. Run the check, review the decisions, and only then download the cleaned file.

Open **Insights**, choose a prompt, and click **Ask agent**. Answers show cited source row IDs. The AQI prompt demonstrates an unsupported-question refusal.

For a forecast, use an actual on-the-hour airport reading from the last four hours. **Use latest airport observation** fills the current report automatically. Weather/model requests now stop with readable errors within 15 seconds. The frozen model estimates temperature at Karachi, Lahore and Multan airports; it is not a neighborhood forecast or an official warning service.
