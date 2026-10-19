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
