"""One Streamlit dashboard: predictions, quality agent, and insight agent."""
import json
import hashlib
from pathlib import Path

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from integration import CITIES, ask_insight, forecast_html, run_quality, training_evidence

ROOT = Path(__file__).resolve().parent
st.set_page_config(page_title="HeatShift · Pakistan", page_icon="☀️", layout="wide")
st.markdown("""<style>
.block-container{max-width:1400px;padding-top:1.5rem}
[data-testid="stMetric"]{background:#edf4f8;border-radius:12px;padding:14px;color:#163047}
button, input, select{min-height:44px}
@media(max-width:600px){.block-container{padding-left:1rem;padding-right:1rem}}
</style>""", unsafe_allow_html=True)
st.title("☀️ HeatShift Pakistan")
st.caption("One dashboard · Temperature prediction · Data quality · Evidence-based insights")
prediction, quality, insights, about = st.tabs(["🌡️ Prediction", "🔎 Data Quality", "💬 Insights", "ℹ️ Project status"])


@st.cache_data
def embedded_forecast():
    return forecast_html()


with prediction:
    st.caption("Waleed’s JMA model remains the default. The station-weather alternative is also available. The model does not learn from dashboard requests.")
    components.html(embedded_forecast(), height=1500, scrolling=True)

with quality:
    st.header("Data Quality Agent")
    st.write("Mateen’s agent checks a CSV. It fixes types, removes exact duplicates, fills short gaps, and flags problems for review.")
    st.warning("This is an offline review. Filled values may use later rows. Do not feed these outputs into forecast training without a separate leakage review. Three rows do not always mean three hours. Raw NOAA TMP/DEW/WND codes are not decoded by this agent.")
    source_mode = st.radio("Choose the data to check", ["Training observations from this project", "Upload a CSV"], horizontal=True)
    data = None
    if source_mode == "Training observations from this project":
        qc_city = st.selectbox("City for quality check", CITIES)
        data = training_evidence(qc_city).to_csv(index=False).encode()
        name = f"{qc_city.lower()}_training.csv"
        st.caption("This checks the measured temperature and time columns. It excludes model targets and held-out data.")
    else:
        upload = st.file_uploader("Upload weather CSV (maximum 10 MB)", type=["csv"])
        if upload is not None:
            data, name = upload.getvalue(), upload.name
        st.caption("Use time and numeric weather columns. Original Open-Meteo exports with three metadata lines are also supported. Do not upload private information.")
    input_key = hashlib.sha256(data).hexdigest() if data is not None else None
    if st.session_state.get("quality_input_key") != input_key:
        st.session_state.pop("quality_result", None)
        st.session_state["approved_cleaned"] = False
        st.session_state["quality_input_key"] = input_key
    if st.button("Run quality agent", disabled=data is None, type="primary"):
        st.session_state.pop("quality_result", None)
        try:
            with st.spinner("Checking your CSV…"):
                report, cleaned = run_quality(data, name)
            st.session_state["quality_result"] = {"report": report, "cleaned": cleaned}
            st.session_state["approved_cleaned"] = False
        except Exception as error:
            st.error(f"Quality check could not finish: {error}")
    if "quality_result" in st.session_state:
        result = st.session_state["quality_result"]
        report = result["report"]
        st.info(f"Last manual quality run: {report['timestamp']} (server clock; time zone not supplied by the agent). File: {report['source']}. This is not an hourly pipeline status.")
        a, b, c, d = st.columns(4)
        a.metric("Rows checked", report["rows_before"])
        b.metric("Duplicates removed", report["duplicates_removed"])
        c.metric("Values filled", report["values_filled"])
        d.metric("Missing values left", report["missing_values_after"])
        st.write(f"Values outside expected ranges: **{report['weather_flags_total']}**. ‘Processed’ means the agent ran; it does not mean every row is safe.")
        for note in report["integration_notes"]:
            st.caption(note)
        if report["decisions"]:
            st.dataframe(pd.DataFrame(report["decisions"]), width="stretch", hide_index=True)
        st.download_button("Download quality report", json.dumps(report, indent=2), "heatshift_quality_report.json", "application/json")
        st.checkbox("I reviewed the decisions. Allow downloading the cleaned copy.", key="approved_cleaned")
        if st.session_state.get("approved_cleaned"):
            st.download_button("Download reviewed cleaned CSV", result["cleaned"], "reviewed_" + report["source"], "text/csv")
        st.caption("Human approval permits a download only. It does not update the warehouse, retrain a model, or issue an alert.")
    with st.expander("Mateen’s uploaded run evidence (historical)"):
        saved = json.loads((ROOT / "evidence/saved_quality_log.json").read_text())
        st.caption("Saved on the agent branch. This is older evidence and is not a fresh run of the copied agent version. Its timestamps have no time-zone label.")
        table = [{"File": x["source"].replace("\\", "/").split("/")[-1], "Status": x["status"], "Rows": x.get("rows_after"), "Missing cells": x.get("missing_values_after"), "Recorded time": x["timestamp"]} for x in saved]
        st.dataframe(pd.DataFrame(table), width="stretch", hide_index=True)

with insights:
    st.header("Insight Agent")
    st.write("Mateen’s agent reads historical training observations. It gives a temperature summary and cites the data rows. It does not predict tomorrow’s weather.")
    insight_city = st.selectbox("City for insight", CITIES)
    question = st.selectbox("What would you like to know?", ["Summarize recorded temperature.", "What are the minimum and maximum recorded temperatures?", "What is the average recorded temperature?", "What is the air quality or AQI?"])
    st.caption("The agent returns its full temperature summary for supported questions. Air quality cannot be inferred from temperature data.")
    if st.button("Ask insight agent", type="primary"):
        st.session_state.pop("insight_result", None)
        try:
            st.session_state["insight_result"] = ask_insight(insight_city, question)
        except Exception as error:
            st.error(f"Insight could not finish: {error}")
    if "insight_result" in st.session_state:
        report = st.session_state["insight_result"]
        st.caption(f"Result for {report['scope']} {report['data_start_utc']} to {report['data_end_utc']}; {report['rows']:,} rows. Last question: {report['question']}")
        if report["answer"]["supported"] and report["citations_valid"]:
            st.success("Supported by the selected historical table. Citation references passed the agent check.")
            st.write(report["answer"]["answer"])
        else:
            st.info(report["answer"]["answer"] if not report["answer"]["supported"] else "I don’t know. Citation checks did not pass.")
        if report["answer"]["citations"]:
            st.dataframe(pd.DataFrame(report["answer"]["citations"]), hide_index=True, width="stretch")
        st.download_button("Download insight and citations", json.dumps(report, indent=2), "heatshift_insight.json", "application/json")
        evidence_city = report["scope"].split(":")[0]
        st.download_button("Download cited training table", training_evidence(evidence_city).to_csv(index=False), f"{evidence_city.lower()}_training_cleaned.csv", "text/csv")
        st.caption("Citation row numbers start at zero and count data rows, excluding the CSV header. The source_row_id column links to the warehouse observation. ‘aggregate’ refers to the whole selected table.")

with about:
    st.header("What is connected")
    st.table(pd.DataFrame([
        {"Part": "Prediction", "Work": "Waleed’s JMA model + station-weather alternative", "Status": "Runs in the prediction tab"},
        {"Part": "Data quality", "Work": "Mateen’s original Python agent", "Status": "Manual run on a separate copy"},
        {"Part": "Insights", "Work": "Mateen’s original Python agent", "Status": "Historical training evidence with citations"},
        {"Part": "Hourly pipeline", "Work": "Organizer evidence / scheduling", "Status": "Not connected; no success claimed"},
    ]))
    st.write("Historical data is not live data. Live JMA retrieval can fail; the prediction tab reports failures explicitly. No model training runs here.")
    st.write("The original agent folder is not changed. The integration loads verified copies from Mateen’s branch and redirects temporary files to a separate workspace.")
    st.write("Recommended: have Mateen review the two agent tabs and Waleed review predictions before final submission.")
    st.json(json.loads((ROOT / "evidence/integration_provenance.json").read_text()), expanded=False)
