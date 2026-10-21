# HeatShift

HeatShift estimates the temperature at the same airport station 24 hours after a recent observation. The public responsive dashboard combines Waleed's existing frozen JMA-assisted model with Mateen's two preserved Python agents. Supported stations: Karachi, Lahore and Multan.

**[Open the Hugging Face dashboard](https://huggingface.co/spaces/Waleed-1234/HeatShift-Dashboard)** | [Submission package](submission/) | [Business model](Business_Model.md) | [Optimization log](OPTIMIZATION_LOG.md) | [AI use log](AI_Use_Log.md)

## What works

- Predictions with a persistence baseline, calibrated error range and input receipt.
- Original Data Quality Agent: duplicate removal, short-gap fill, flags and quality_log.
- Original Insight Agent: numeric table summaries plus keyword retrieval from trusted notes, row/section citations and unsupported-question refusals. This is lightweight deterministic RAG, not a general LLM chatbot.
- Hourly GitHub Actions: fetch METAR/JMA, review, predict, cite, retain raw/cleaned/processed data, manifest and SQLite; publish runtime/latest.json. Scheduling and upstream requests can be delayed. Check [Actions](https://github.com/waleedirfan2006-arch/Heat-Shift-/actions).
- Static browser agents keep uploaded CSVs in the visitor's browser. First use downloads Python/pandas and can take about a minute.

## Reproduced evaluation (21 October 2026)

The primary is **HistGradientBoosting**, not the early Ridge experiment. On the same 1,783 reused validation rows, model MAE **1.101946 C** vs declared raw-temperature persistence **1.235165 C** (10.8% observed reduction). The rounded deployment baseline is separately **1.243915 C**. January was worse than persistence; the seven-day block-bootstrap improvement interval **[-0.0417, 0.2707] C** includes zero. Do not describe this as independent final-test proof.

| Group | Rows | Model MAE | Raw baseline MAE |
|---|---:|---:|---:|
| Karachi |419|1.031|1.368|
| Lahore |963|1.082|1.129|
| Multan |401|1.226|1.352|
| January 2024 |775|1.165|1.074|
| February 2024 |1008|1.053|1.359|

March nominal 90% calibration bands: Karachi +/-2.224 C (183 rows), Lahore +/-3.084 C (398), Multan +/-2.271 C (174). Future coverage is not guaranteed. [Receipts, row IDs and metrics](evidence/final_audit/primary_model/). No new locked-test/replay/reserve scoring or retraining occurred.

## Reproduce and run

With Python 3.12, pandas and GNU make installed, from repository root:

```sh
python -m pip install pandas==2.2.3
make data
```

The command rebuilds the warehouse in automation/runs/historical by default; set WORKDIR to choose another output. Existing authoritative warehouse files stay preserved. The hourly workflow verifies the same command on Ubuntu for manual/push runs. On Windows without make, use the equivalent Python warehouse command documented in the Makefile.

For a one-off live run, install Node 22 as well:

```sh
python automation/hourly_pipeline.py --output automation/runs
```

To serve the static source locally, first run python HeatShift_Web/download_runtime.py, then serve HeatShift_Web with a local HTTP server. The runtime downloader pins official Pyodide 0.27.7 assets and checks SHA256. Never publish user CSVs or credentials.

Reproduce frozen-model validation/calibration (network required; reads only those two splits): python automation/evaluate_frozen_primary.py. Original JMA model fitting feature table/search records are unavailable, so full fitting reproducibility is incomplete.

## Submission and honest limitations

See [SUBMISSION_CHECKLIST.md](SUBMISSION_CHECKLIST.md). Required PDFs are in submission/, including organizer-spelled datasetpropsal.pdf and one-page Summary.pdf. The latest event notice explicitly requires slides and a Devpost link; Project_Explanation_Viva.pdf supplies a simple speaking outline. Every team member must attend the physical viva.

Some original Open-Meteo collection metadata and original JMA fitting evidence remain unverified. Airport weather is not every neighborhood's weather. This is a temperature prototype, not rain/pollution forecasting or an official warning service. Commercial use needs appropriate source rights and service planning.

Mateen's original copies remain under HeatShift_Unified_Space/vendor/; adapters verify their fingerprints. Historical experiments and audit files remain available under their original folders. Read AI_Use_Log.md for substantial AI assistance and pending human review.


## Team contributions

Roles provided by Waleed Irfan on 21 October 2026:

| Team member | Responsibilities |
|---|---|
| **Waleed Irfan** | Developed the prediction model and worked on improving it. |
| **Syed Mateen Ali** | Developed, managed and maintained both AI agents: the Data Quality Agent and the Insight Agent. |
| **Aman Khan Lodhi** | Responsible for data cleaning, data warehouse management and related data preparation. |

These responsibilities are the team's reported contribution allocation. Substantial AI assistance is documented separately in `AI_Use_Log.md`; the allocation does not remove that disclosure or imply that every line was written without assistance.


## Final audit disclosures

See [final checklist](SUBMISSION_CHECKLIST.md): historical Prefect export/screenshot missing; declaration late; some original source/fitting records unverified. Strict Insight scope and source row IDs are implemented. Operational refreshes use heatshift-runtime so final code can stay frozen. Slides and a Devpost link are required by the latest notice.
