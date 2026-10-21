---
title: HeatShift Pakistan Unified Dashboard
emoji: ☀️
colorFrom: orange
colorTo: blue
sdk: docker
app_port: 7860
pinned: false
---

# One HeatShift dashboard

Three working areas in one Streamlit app: temperature prediction, Mateen’s Data Quality Agent, and Mateen’s Insight Agent.

## Run on your computer

Use Python 3.12. Open a terminal inside this folder.

```bash
python -m venv .venv
# Windows Git Bash:
.venv/Scripts/python.exe -m pip install -r requirements.txt
.venv/Scripts/python.exe -m streamlit run app.py
```

On Linux, use `.venv/bin/python` instead. Open the local address printed by Streamlit.

## Deploy to Hugging Face

Recommended: keep one Space for the final project. This is a **Docker Space running Streamlit**, not a static HTML Space. Upload the **contents of this folder** to the Space root. Include `Dockerfile`, `README.md`, `app.py`, `integration.py`, `requirements.txt`, and the complete `prediction`, `vendor`, and `evidence` folders. Do not upload the outer folder as another level. Replace the root README with this README so `sdk: docker` and `app_port: 7860` are applied. Do not keep a static SDK setting for this app. Wait for the Docker build and Running state. Refresh the App tab.

The Dockerfile runs Streamlit on port 7860 as a non-root user. No paid hardware, secret key, or model training is needed. Existing root static files are unused by this Docker app. Changing the existing Space SDK replaces the old app; use the previous commit to roll back if needed.

## What each tab does

| Tab | Input | Output |
|---|---|---|
| Prediction | Recent airport report | 24-hour temperature estimate, baseline and error range |
| Data Quality | Training observations or uploaded CSV | Actual agent decisions, report and approved cleaned download |
| Insights | City and a supported question | Actual agent answer with historical table citations |
| Project status | Saved source details | Scope and remaining integration work |

The prediction UI comes from the tested release `054a96819cd40b3c568b2c45851c03d15095ffc1`. A later merge on main duplicated JavaScript declarations, handlers and HTML IDs. The integration repairs those four shared UI files by restoring that tested version. Trained model parameters are unchanged. Its three modes remain: Waleed’s original JMA default, the station-weather alternative, and an explicit persistence baseline. The offline alternative does not need an external weather fetch after manual observation entry. External JMA requests still depend on service availability and browser CORS behavior.

## Mateen’s code is preserved

`vendor/data_quality_agent.py` and `vendor/insight_agent.py` are byte-identical copies from commit `165be6f1a61130e42099f9b30683f29d4820e22b`, branch `add-airguard-agent-folder`. Their SHA-256 hashes are checked before loading. The original `AirGuard_Agent` path is untouched. Main currently has an empty placeholder at that path, so copying only main would not recover the agents.

The adapter configures isolated temporary folders because the original agents expect different folder names and casing. It calls the original `process_file()` and `ask()` methods. It does not replace their decision rules. Explicitly zoned timestamps are converted to UTC without a suffix in the temporary copy to avoid the agent’s naive-versus-aware date subtraction error. This conversion is disclosed in the report. Unreliable server-local data age is returned as unknown. Agent outputs are never sent into trained-model inputs automatically.

## Data and limitations

The three compressed city tables contain only the 16,463 training observations’ current temperature, UTC time and source row ID. No target values, validation, locked test, replay or reserve data are included. They are historical, not current weather. They are derived from Amaan’s/Waleed’s existing warehouse. See `evidence/integration_provenance.json` for the source fingerprint.

The quality agent fills up to three missing rows using linear interpolation. Rows may not be evenly spaced. It can use later values. Its output is for offline review, not automatically safe for prediction training. It does not decode raw NOAA composite fields or guarantee a complete quality audit. Its timestamp is a naive server-clock value; no time zone is invented. Empty decisions do not prove all data is valid.

The insight agent supports numeric summaries of the selected training table. It is not a general-purpose chatbot or another trained forecast model. It refuses air-quality questions without pollutant data. Citation checks confirm references exist, not that every possible question is semantically answered.

Saved quality evidence is from the older uploaded run; it is clearly separated from new manual runs. New outputs live only in the current session unless downloaded. Space restarts clear temporary data. This app does not implement or claim hourly scheduler/fetch evidence or official warnings.

## Human review

Recommended: Mateen verifies agent behavior, Waleed verifies the forecast output, and Amaan verifies the combined dashboard and upload. The cleaned download requires a review checkbox. It does not trigger a risky action or replace the warehouse.
