# AI Use Log — HeatShift Pakistan

Date: 19 October 2026, Pakistan time.
Assistant: ChatGPT in Codex Work Mode.
Exact underlying model/version: not available to the assistant; do not invent one.
Project: Climate and heat-health — HeatShift Pakistan.
Team size: 3. The user confirmed that three-person teams are allowed on 19 October 2026.

Repository: https://github.com/waleedirfan2006-arch/Heat-Shift-
User's local project: D:\Heat-Shift-
User's warehouse folder: D:\Heat-Shift-\HeatShift_Warehouse

## Team progress reported on 19 October 2026 at 23:06 PKT

The user reported committing 42 files in commit 8f3e9f1, pushing branch add-heatshift-dataset, merging PR #1, pulling main and confirming a clean working tree matching origin/main. The user added warehouse.sqlite to .gitignore because of the repository file-size limit.
These Git actions were performed by the team, not this assistant. The public repository could not be fetched through the available web lookup, so this log records the update as user-reported.
The revised package described below has not been verified as copied or committed to the team's repository. Follow GITHUB_UPDATE.md to add it.
The user reports that no full dataset-quality audit, leakage assessment, model-readiness review or model training has been performed. Earlier assistant checks were limited warehouse engineering checks; they do not replace those reviews.

This log was drafted by the assistant. Team review and understanding are still required.
It describes substantial AI assistance, including complete runnable warehouse code.
It does not claim that students independently wrote that code.

## Material assistance

| Work | What the assistant did | Included work | Checks actually performed | Human owner/review |
|---|---|---|---|---|
| Project planning | Read the provided guide/poster; proposed HeatShift, a simple baseline, chronological splits and a build plan. | Earlier playbook; current source and model documentation. | Compared requirements with the provided documents. | Recommended: C; name and review pending. |
| Source research | Located NOAA and Open-Meteo documentation and explained source limits. | SOURCES_AND_RULES.md, DATASET_SHEET.md. | Opened official documentation; examined uploaded files. | Recommended: A; name and review pending. |
| Initial warehouse | Wrote the complete Python cleaning/build script, SQLite tables, CSV exports and model examples. | build_warehouse.py, warehouse.sqlite, cleaned/final exports. | Raw hashes, timestamps, exact 24-hour targets, past input joins, database integrity and repeated rebuild comparisons. | Recommended: A; name and review pending. |
| Data preparation | Decoded NOAA temperature codes; handled missing/quality-flagged readings and repeated reports; retained gaps and record IDs. | Script and quality logs. | Checked source encoding documentation; verified target/source links. | Recommended: A; name and review pending. |
| Source completion | Re-downloaded 12 NOAA station/year files for 2022–2025; added the 3 previously missing 2022 files; recorded actual receipt times and hashes. | manifest.csv/json, evidence/fetch_receipts.json, raw NOAA snapshots. | All 9 overlapping downloads matched the supplied original bytes. | Recommended: A; name and review pending. |
| Rebuild completion | Wrote runnable snapshot restore, build runner and source-verification script. | pipeline.py, fetch_sources.py, Makefile, source_snapshots.zip. | See quality/completion_verification.json for tests actually completed. | Recommended: B; name and review pending. |
| Documentation | Drafted the declaration, updated file guide, status and instructions for the unfinished stages. | Dataset_Declaration_DRAFT.md, COMPLETED_AND_NEXT.md, HOW_TO_BUILD_DQ_AGENT.md, REMAINING_STEPS.md, this log. | Checked facts against code, source records and actual task outputs. | Recommended: C; name and review pending. |

## What was not done

- No Data Quality Agent was implemented in this update, as the user requested.
- No prediction model was trained or scored. No model improvement is claimed.
- No retrieval/generative assistant was built or evaluated.
- No hourly scheduler, cloud deployment, organizer message, repository commit or submission was performed.
- No original Open-Meteo download time or exact request/model setting was invented.
- No demonstration, performance result, user approval or completed team review was fabricated.

## Important decisions and limits

- The final-test dates stayed fixed. Adding 2022 supplies the originally planned training period; it is not a response to test scores.
- Open-Meteo is historical comparison data, not a prediction input or a replacement for missing station targets.
- Uploaded originals are retained in evidence/original_uploads.zip, with their original manifest.
- New NOAA collection times describe new fetches. They do not rewrite the history of the original uploads.
- Automatic checks performed by an assistant are not a substitute for students understanding the code.
- The provided PDF contains both a statement allowing disclosed AI assistance and appended instructions restricting complete AI code. The user requested runnable implementation. Record the actual assistance and confirm applicable competition policy if needed; do not describe the code as merely a skeleton.

## Team review — fill only after doing it

| Person | Files they can explain | What they checked or changed | Review date |
|---|---|---|---|
| To fill | To fill | Pending | Pending |
| To fill | To fill | Pending | Pending |
| To fill | To fill | Pending | Pending |

Recommended review exercise: each student explains one real raw record, its cleaned value, its final-table use and the reason another record was rejected. Then one student runs make data in a fresh folder and another checks the printed counts.

## Future entries

For every later AI-assisted task, add the date, tool/model if known, task, code/text kept or changed, actual tests and the person who can explain it.

---

## Update added on 20 October 2026

The earlier entries above describe the work at that time. The following entry records the later audit; it does not claim a new model training run or completed human review.

# AI assistance record

The cumulative record is in [HeatShift_Warehouse/AI_Use_Log.md](HeatShift_Warehouse/AI_Use_Log.md).

## Data-quality and leakage review — 2026-10-20T04:33:32.124744+00:00

- User requested a full review, source-evidence completion, updated files and GitHub upload if possible.
- Assistant inspected base commit ffdecac496688f8257741f69ac61d693be53ace2, all raw/clean/final tables and training code.
- Authored independent audit code, reports, pre-training guards and copy-only stress tests. These are substantial AI-written contributions.
- Verified hashes, exact time joins, split boundaries, preprocessing placement and fresh rebuild outputs. No model trained/scored, no agents implemented, no data values/split windows changed.
- Checked official Open-Meteo documentation/licence and completed supported manifest fields. Original URL, selected model and download timestamp remain Unverified without collector evidence.
- Fixed stale hardcoded training-period text; added input hashes and guard checks. Waleed must review before training.
- Human review: pending. Team members must record their own review honestly.
- GitHub action status is recorded in AUDIT_UPDATE.md / delivery message; do not infer publication from this log.

## Log merge — 20 October 2026

The assistant preserved the uploaded root assistance log and appended the audit record. The installer now checks against that reviewed uploaded log before replacing it. No other installer checks were removed.

## Live-system review — 21 October 2026 PKT
Assistant inspected public main, Space source and accessible shared-chat content (plugin outputs redacted). Authored browser inference/input-validation fixes, prediction receipt UI, regression fixtures and HeatShift_Static_Space/REVIEW.md. Verified exported model equality, 51 Python/JS inference cases (max difference zero), and 9 form checks. No new model trained or accuracy improvement claimed. Final publication and human review pending. Training/evaluation reproducibility gaps are documented.

## Training and interactive website — 21 October 2026 PKT
User requested improvement of Waleed's model and website only. Assistant trained and compared eight station-only ML configurations plus persistence on three expanding training folds, selected HGB 250 iterations/7 leaves, fitted it on all 16,463 training rows, and scored fixed validation (1,783 rows). MAE was 1.237479 C versus baseline 1.235165 C, so it was not promoted over the existing JMA primary. No locked-test, replay or reserve scoring/tuning was performed. Artifacts, input hashes and row-level validation predictions are in HeatShift_Training/station_results.
Assistant authored the redesigned HTML/CSS/JavaScript dashboard, METAR parser, explicit baseline mode, unit/theme controls, session history, source display and JSON downloads. Agent files unchanged. Human review pending. GitHub/Space publication state must be verified separately.


## 2026-10-21 — Unified dashboard integration

At Amaan’s request, ChatGPT/Codex integrated Mateen’s unchanged Data Quality and Insight agents from branch commit 165be6f into a Streamlit dashboard alongside Waleed’s JMA predictor and the station-weather alternative. AI authored the adapter, dashboard, deployment configuration, documentation and integration tests. The adapter isolates writes and normalizes explicitly zoned timestamps; it does not change the vendor source. AI also restored four forecast UI files to tested commit 054a968 after detecting duplicate declarations/DOM elements introduced by a later merge. Training-only evidence was derived from the existing warehouse, excluding targets and held-out data. Nine Python integration tests, twelve embedded forecast DOM checks, and thirty-two existing input/parser checks passed. No retraining or production deployment is claimed. Amaan, Waleed and Mateen’s further review is recommended and is not recorded as completed.


## 2026-10-21 - Final submission and public Space work

At Waleed's explicit request, Codex inspected the repository and public Space, preserved both Mateen vendor source fingerprints, and authored substantial browser integration, document retrieval setup/guards, calibrated range display, hourly pipeline, workflow, build target, tests, documentation and submission artifacts. AI created the summary, dataset proposal, business model, viva guide and captioned demo from actual dashboard views. These are AI-assisted artifacts.

The frozen JMA model was not refitted. AI reproduced 1,783 validation predictions and 755 March calibration predictions using freshly fetched archived JMA fields with receipts, and recorded row-level errors and a block bootstrap. Locked-test, replay and reserve data were not opened/scored during this final audit. Warehouse rebuild passed 14 checks. Nine relevant adapter tests and the hourly failure test passed; the legacy Streamlit UI test was not run because Streamlit is unavailable locally. Browser checks validate the deployed static UI separately.

Missing original collection metadata and original JMA fitting/search records remain explicit. Exact human effort and original training resource use are unknown. No paying customers or measured social impact are claimed. Human contribution review, correction of inaccurate authorship statements, source/license confirmation and all-member viva attendance remain team responsibilities. No human sign-off is fabricated. Publication is verified in release/delivery records; workflow execution must be checked separately.

Publication verification: the public Space update was confirmed live; first Actions run 39608434792 succeeded, including make data and status publication. A clock-triggered hourly event has not yet been observed at this point.


## 2026-10-21 - Team contribution clarification

Waleed explicitly supplied the team roles: Waleed Irfan developed and improved the prediction model; Syed Mateen Ali developed, managed and maintained both the Data Quality and Insight agents; Aman Khan Lodhi handled data cleaning, warehouse management and related data preparation. Codex added this allocation to the four submission PDFs, README, business-model document and team/AI summaries. These are user-reported responsibilities, not an independent authorship audit. Earlier AI-assistance disclosures and pending human-review notes remain in force. No model or agent code was changed.


## 21 October 2026 — Strict insight scope and final requirements audit

Codex added a strict complete-question policy around the unchanged Mateen Insight Agent. It verifies canonical table hashes, records original source IDs and numeric aggregation claims, and permits selected source-cited project guidance. Unsupported locations, date filters, future weather and personal recommendations refuse. The restricted grammar may also refuse reasonable paraphrases. Original agent vendor files and frozen model parameters remain unchanged. No fitting or new locked/replay/reserve scoring was done.

Thirteen adapter/scope tests, one failure-path test and one status-publication mock passed. Browser execution verified historical statistics with original NOAA IDs, unsupported Islamabad refusal and sourced uncertainty explanation. The clean-start warehouse passed fourteen checks. The legacy Streamlit UI test remains unrun locally. Existing timing benchmarks predate this policy and are not measurements of the new checks.

AI changed hourly publication to a separate operational branch, added explicit failure/freshness/last-success reporting, and verified a successful real Actions run. AI inspected fourteen branches and declaration/baseline commit history: no historical Prefect export/screenshot was found and the declaration draft was late. These items are disclosed, not fabricated or marked fulfilled. Original fitting and some collection records remain unavailable.

AI updated four PDFs, the checklist, source manifests, demo captions, presentation packaging and release preparation. The saved demo is an actual-dashboard screenshot sequence without voice narration, not a continuous live recording. Human review, Devpost submission and all-member viva attendance are not invented. Team roles were supplied by Waleed, not independently certified authorship. No organizer message was sent.


## 21 October 2026 — Requested prediction time-field correction

At the user's request after the previous final release, Codex removed the browser-native datetime step popup and routed form errors through the existing explicit model validation. The time field accepts minute entry for clear inline feedback; the unchanged hourly model still requires actual on-hour observations from the last four hours. The UI points users to the verified latest-observation fill button. No observation is silently rounded or invented, and model parameters remain unchanged. The final tag is refreshed only after verification of this requested fix.


## 21 October 2026 — Dashboard guidance and bounded prediction

At Waleed's request, Codex added plain-language steps for selecting a CSV, reviewing the Data Quality Agent decisions, asking the Insight Agent, and filling a current airport observation for prediction. Added a real 5,012-row Karachi training CSV and a separate, clearly labeled synthetic QA exercise. It contains one duplicate, two internal missing readings, a four-row missing run and one out-of-range value. The preserved Mateen agent reported one duplicate removed, two filled values and one range flag; it left the long gap missing. The fixture is not weather evidence.

The frozen model and original agent code are unchanged. Model, calibration and JMA requests now have time limits; failures restore the button and show a readable message. The existing on-hour and last-four-hours observation requirements remain. JavaScript syntax checks passed, off-hour and stale-input messages were checked, and the practice CSV was processed by the original agent.


## 21 October 2026 — Dashboard guidance and bounded prediction

At Waleed's request, Codex added plain-language steps for selecting a CSV, reviewing the Data Quality Agent decisions, asking the Insight Agent, and filling a current airport observation for prediction. Added a real 5,012-row Karachi training CSV and a separate, clearly labeled synthetic QA exercise. It contains one duplicate, two internal missing readings, a four-row missing run and one out-of-range value. The preserved Mateen agent reported one duplicate removed, two filled values and one range flag; it left the long gap missing. The fixture is not weather evidence.

The frozen model and original agent code are unchanged. Model, calibration and JMA requests now have time limits; failures restore the button and show a readable message. The existing on-hour and last-four-hours observation requirements remain. JavaScript syntax checks passed, off-hour and stale-input messages were checked, and the practice CSV was processed by the original agent.

## 21 October 2026 — Live dashboard smoke test

The public Space was tested end to end after the CSV guidance update. Downloading and reselecting the labeled synthetic practice file worked. In a new tab, the first original-agent startup took about two minutes; keep a warmed tab open for a short judge demo. Mateen's unchanged agent reported 1 duplicate removed, 2 short-gap values filled, 1 out-of-range value flagged and 4 long-gap values left missing. A cited Karachi temperature answer and an unsupported AQI “I don't know” answer both worked. The live frozen model returned 30.2 °C for 22 Oct 20:00 PKT from a 30.0 °C manual test observation at 21 Oct 20:00 PKT, with 10/10 JMA fields. The manually supplied test input is labeled as such; it is not represented as a newly observed measurement. No model or agent source was changed.
