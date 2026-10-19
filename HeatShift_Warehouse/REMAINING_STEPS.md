# Remaining HeatShift work — Recommended plan for 3 students

Keep one project: HeatShift Pakistan. Keep one model: Ridge regression.
Ridge regression is a simple method that learns a weighted combination of inputs.
This file gives instructions. It does not claim the remaining stages are built.

## Who does what

| Student | Main work | Also check |
|---|---|---|
| A: basic ML/data | Data Quality Agent, temperature model and fair evaluation | Source records and missing values |
| B: web/backend | Hourly scheduler, SQLite access and dashboard | Freshness, failed runs and hosting |
| C: writing/presenting | Trusted documents, assistant tests, evidence and demo | Citations, AI log and usability |

The user confirmed a three-person team is allowed. No fourth person is required in this plan.

## First: finish evidence and set up the scheduler early

- [ ] Recover the original Open-Meteo download URL/settings and timestamp if available. Do not invent them.
- [ ] Preserve the real Dataset Declaration commit. The draft in this package is not proof of a noon submission.
- [ ] Review the new NOAA 2022 files against the declaration before training. They restore the original planned training window.
- [x] Earlier 42-file warehouse committed as 8f3e9f1 and PR #1 merged, as reported by the user at 23:06 PKT on 19 October.
- [ ] Apply this newer package using GITHUB_UPDATE.md and review AI_Use_Log.md. No repo was changed by the assistant.
- [ ] Start building the real hourly flow now, alongside the agent/model work. Do not wait until the deadline.

Required run evidence: Tuesday 20 October 2026, 4 PM PKT through Wednesday 21 October 2026, 4 PM PKT. In UTC: 20 October 11:00 through 21 October 11:00.

## Stage 4: train and evaluate

1. Read 02_final/model_contract.json. Use only its listed input columns.
2. Load train.csv. Fill optional older-temperature blanks using a median learned from training only. The median is the middle value. Retain the missing flags.
3. Convert station, hour and month categories into yes/no columns. Fit this conversion on training only.
4. Fit any numeric scaling on training only. Scaling puts numbers on comparable ranges.
5. Fit Ridge. Use time-ordered checks inside training and validation.csv for choosing settings. Save each choice and measured result.
6. Compare with the fixed baseline: predicted temperature 24 hours later equals current temperature.
7. Measure MAE: the average size of the prediction error in Celsius. Compare both methods on exactly the same rows.
8. Freeze the model and settings. Use calibration.csv to estimate an error range from its absolute errors, as described in the earlier playbook. Label it an empirical range, not a guarantee.
9. Run test_locked.csv once for the final report. Report MAE, interval coverage/width and errors by city, month and time of day. State each group size.
10. If the model loses to the baseline, report that honestly. Do not change the locked test or pick a different baseline after seeing the result.

Keep replay.csv and reserve_2025.csv out of tuning. Never use the future target column as an input. Model input preparation must be saved with the model so the app uses exactly the same rules.

Suggested proof files: model.joblib, model_card.md, metrics.csv, group_errors.csv, interval_report.csv and optimization_log.csv.
An optimization log records what changed, error, time, memory and whether the change was kept. Make one change at a time. Measure real values; leave unmeasured fields blank.

## Stage 5: retrieve evidence

RAG means finding supporting evidence before writing an answer.

1. Collect a small permitted library of official heat guidance and your model card.
2. Start with NWS guidance: https://www.weather.gov/safety/heat-during . Check reuse terms. Add Pakistan-specific material only when its use is permitted.
3. Split documents by headings. Store source URL, title, section and section ID with every piece.
4. Recommended: multilingual MiniLM embeddings and FAISS. Embeddings are numerical descriptions of text; FAISS searches them. Add a simple keyword search and rerank the best combined matches, as the poster asks.
5. Query SQLite for the requested city and historical time. Return matching gold-table row IDs with the document sections.
6. Save this evidence bundle for each question. An evidence bundle is the material supporting one answer.

Do not reveal replay records later than the current simulated clock. Historical comparison data must be marked as hindsight and must not become forecast inputs.

Suggested proof files: documents_manifest.csv, evidence_bundles.jsonl and retrieval_tests.csv.

## Stage 6: generate cited answers

1. Recommended first model: Qwen2.5-0.5B-Instruct. Test its speed and answer quality on your actual machine; neither is verified here.
2. Give it only the retrieved evidence. Ask for short wording with source-section IDs.
3. Insert all numerical results from SQLite using code. Reject unexpected numbers and unsupported claims.
4. If evidence is missing, answer: "I do not have enough evidence for that answer."
5. Keep the prompt version, evidence IDs, answer and check result. A prompt is the instruction sent to the language model.
6. Test questions with evidence, without evidence and misleading questions. Record actual citation correctness, number agreement and refusal quality.
7. Add human-reviewed Urdu interface text. Test generated Urdu before claiming it works reliably.
8. Put briefs or risky recommendations into a pending-review queue. Show approved content only after a person records approval.

Do not claim a template-only answer is a working generative agent. Do not make medical predictions or certify safe working conditions from air temperature alone.

Suggested proof files: prompts/, golden_qa.csv, generative_eval.csv, answer_logs.jsonl and approval_log.csv.
A golden Q&A set is a small, human-checked set of questions and expected evidence or refusals.

## Stage 7: run hourly, publish and deliver

1. Use Prefect on a laptop or reliable server that stays on. Prefect schedules and records workflows.
2. Build a flow: advance one historical replay batch, check data, run the frozen model, refresh evidence/answers and update the dashboard.
3. Record real run times and statuses. Keep original event times separate. Repeated replay runs are not new weather observations.
4. Set retries. Make repeating the same batch safe: no duplicated records. Do not retrain each hour. Review drift and only promote a candidate after an honest comparison on eligible validation data.
5. Schedule every hour. Test the exact first run and the required start/end window. If using five minutes past each hour, confirm that evidence covers the organizer's expected window.
6. Keep the laptop awake, plugged in and connected. Take genuine Prefect dashboard evidence. Never manufacture missing runs or edit failures out of the export.
7. Confirm the expected prefect_runs.csv export format with organizers if unspecified. Save the unedited real history and a dashboard screenshot.
8. Publish Gradio or Streamlit on a Hugging Face Space as required. Check account access immediately; free hosting availability is not verified for your account. An organizer-provided Space may be needed. Vercel/Render alone is not the required Space submission unless organizers approve it.
9. Show historical data date, last source fetch, gaps, agent status, model/baseline metrics, citations and last successful run. All numbers must come from current stored tables.
10. Finish the one-page Summary.pdf, a video no longer than 3 minutes, AI_Use_Log.md, model card, quality report, generative tests and optimization notes. Tag the final GitHub commit v1.0-final after all judged files are present.

Submission deadline: Wednesday 21 October 2026, 11:59 PM PKT; the guide says the form closes at 12:00 AM Thursday. Every member must prepare for the physical viva.

## Simple work order

Tonight, after the reported 23:06 PKT update: apply this revised package and confirm its rebuild; address source evidence and declaration history; start agent work and real Prefect setup across the three students. Do not claim a completed audit or begin locked-test evaluation just because the files are on GitHub.
Tuesday morning: finish agent integration, model selection and the first dashboard; begin evidence retrieval.
Before Tuesday 4 PM: the genuine hourly scheduler must be ready and running for the evidence window.
Tuesday evening/Wednesday: finish cited answers, tests, UI and proof files while the scheduler continues.
Wednesday after the evidence window: export real history, finish the demo and final review, then tag and submit before the deadline.

## Official references checked on 19 October 2026

- Pandera: https://pandera.readthedocs.io/en/stable/
- Ridge: https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.Ridge.html
- Prefect local server: https://docs.prefect.io/v3/how-to-guides/self-hosted/server-cli
- Hugging Face Spaces: https://huggingface.co/docs/hub/spaces-overview
- Qwen model: https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct
- Embedding model: https://huggingface.co/sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2

Tool choices and implementation details in this document are Recommended. Competition obligations come from the provided guide/poster. No model, runtime, cost, win or score is promised.
