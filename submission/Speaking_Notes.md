# HeatShift speaking notes

Present slides 1-8 in six minutes including the two-minute live demo. Leave slide 9 visible for questions. Slides 10-12 are backup material. The full slot is ten minutes including questions.

## Slide 1: 

WALEED | 15 seconds | 0:00-0:15
Hello, we are the HeatShift team. Our project helps people understand tomorrow’s temperature and the evidence behind it. We combine a prediction model with two agents in one dashboard. Our current scope covers three airport stations.

Sources:
https://github.com/waleedirfan2006-arch/Heat-Shift-/blob/main/TEAM_CONTRIBUTIONS.md
https://github.com/waleedirfan2006-arch/Heat-Shift-/blob/main/README.md

## Slide 2: The problem and our solution

WALEED | 25 seconds | 0:15-0:40
We focused on making a forecast easier to judge. A number alone does not show whether its data is complete or where an explanation came from. HeatShift puts the prediction, quality checks and evidence references together. Everyday users are our intended audience. We have not yet measured the impact on their decisions.

Sources:
https://huggingface.co/spaces/Waleed-1234/HeatShift-Dashboard
https://github.com/waleedirfan2006-arch/Heat-Shift-/blob/main/Business_Model.md

## Slide 3: The data warehouse

AMAN | 35 seconds | 0:40-1:15
I handled data cleaning and warehouse management. We keep original files, cleaned data and processed tables separate. A manifest records where files came from and their fingerprints. We use time-based splits because future weather must not leak into training. The single make data command rebuilds the warehouse. The final audit passed fourteen checks. Some original collection receipts remain unavailable.
Live METAR data supplies current inference inputs, not historical model training. Open-Meteo historical comparison snapshots are distinct from JMA previous-runs features.

Sources:
https://github.com/waleedirfan2006-arch/Heat-Shift-/blob/main/submission/datasetpropsal.pdf
https://github.com/waleedirfan2006-arch/Heat-Shift-/blob/main/evidence/final_audit/warehouse_rebuild_receipt.json
https://www.ncei.noaa.gov/products/land-based-station/integrated-surface-database
https://open-meteo.com/en/docs/previous-runs-api

## Slide 4: The prediction model

WALEED | 35 seconds | 1:15-1:50
I developed the model and worked on improving it. The deployed model is HistGradientBoosting, which combines small decision trees to correct prediction errors. It uses the current station temperature, JMA forecast fields and calendar information. It predicts a correction to the current temperature for the same hour tomorrow. We compare it with a simple rule: tomorrow equals today. This audit preserved the existing model parameters.
The earlier Ridge and station-only alternatives did not beat persistence. Original JMA fitting-feature and search records remain unavailable. Do not claim full training reproducibility.

Sources:
https://github.com/waleedirfan2006-arch/Heat-Shift-/blob/main/HeatShift_Web/core.js
https://github.com/waleedirfan2006-arch/Heat-Shift-/blob/main/HeatShift_Web/model.json
https://github.com/waleedirfan2006-arch/Heat-Shift-/blob/main/OPTIMIZATION_LOG.md

## Slide 5: Mateen’s two agents

MATEEN | 40 seconds | 1:50-2:30
I developed, managed and maintained both agents. The quality agent reviews missing values, duplicates and unusual weather readings, then records its decisions. Its short-gap interpolation can use later rows, so we review cleaned data before modeling. The insight agent retrieves trusted notes and calculates statistics from the training tables. It gives row or section citations. This is lightweight deterministic RAG. It refuses questions when the data does not support an answer.
Both original vendor files retain their source fingerprints. Browser adapters verify them before execution. This is not a general LLM chatbot.

Sources:
https://github.com/waleedirfan2006-arch/Heat-Shift-/blob/main/TEAM_CONTRIBUTIONS.md
https://github.com/waleedirfan2006-arch/Heat-Shift-/tree/main/HeatShift_Unified_Space/vendor
https://github.com/waleedirfan2006-arch/Heat-Shift-/blob/main/HeatShift_Web/trusted_weather_guide.md

## Slide 6: Live demonstration

TEAM | 120 seconds | 2:30-4:30
Switch to the already-open dashboard. Do not play the full backup video as well as a live demo.
0-30 seconds, Waleed: select a city, use the latest automatic observation and run a prediction. Point to the timestamp, baseline and calibrated range. If no fresh observation is available, show the saved example and say it is historical.
30-60 seconds, Aman: show the hourly status and its timestamp, then open data quality. Mateen runs or shows the completed check and explains one decision.
60-90 seconds, Mateen: ask for a temperature summary and point to the row and section references.
90-120 seconds, Mateen: ask about AQI and show the refusal. Return to the slides.
Preload Python agents before your turn. If the network fails, use HeatShift_Demo.mp4 or the screenshots in this deck and identify their capture date. Never imply a saved example is current weather.

Sources:
https://huggingface.co/spaces/Waleed-1234/HeatShift-Dashboard
https://github.com/waleedirfan2006-arch/Heat-Shift-/blob/main/submission/DEMO_README.md

## Slide 7: Lower average validation error

WALEED | 55 seconds | 4:30-5:25
MAE means average absolute error in Celsius. Across the same 1,783 validation examples, the model had about 1.10 degrees of error compared with 1.24 for repeating today’s temperature. That is 10.8 percent less average error. It is not a percentage accuracy score. January was worse, and the bootstrap interval includes no improvement. We show March-calibrated uncertainty ranges, but future coverage is not guaranteed. These are reused validation results, not a fresh independent final test.
Declared unrounded baseline MAE: 1.2351654514862591 C. Rounded deployment baseline: 1.2439147504206394 C. Model: 1.1019464086208355 C. Seven-day block bootstrap 95% improvement interval: [-0.0416937705, 0.2706989324] C. No new locked-test, replay or reserve scoring in the audit.

Sources:
https://github.com/waleedirfan2006-arch/Heat-Shift-/blob/main/evidence/final_audit/primary_model/metrics.json
https://github.com/waleedirfan2006-arch/Heat-Shift-/blob/main/evidence/final_audit/primary_model/row_predictions.csv

## Slide 8: Feasibility and business model

WALEED | 35 seconds | 5:25-6:00
The basic dashboard serves everyday users. Institutions could eventually pay for reporting and support. That is a business proposal, not existing sales. The current prototype uses a free static Space and public GitHub Actions, subject to their terms. A commercial service would need appropriate weather API rights and a maintenance budget. We want to measure whether users understand forecasts better before claiming real-world impact.
Commercial previous-runs access needs the appropriate Open-Meteo plan. No price or paying customer has been validated. The existing final audit records a successful push-triggered hourly-workflow run; schedule delays remain possible.

Sources:
https://github.com/waleedirfan2006-arch/Heat-Shift-/blob/main/Business_Model.md
https://open-meteo.com/en/pricing
https://github.com/waleedirfan2006-arch/Heat-Shift-/blob/main/evidence/final_audit/first_actions_run.json

## Slide 9: Team contributions and questions

QUESTIONS | 6:00-10:00
Stop the main presentation at six minutes. Leave this slide visible for judges’ questions. Roles come from Waleed’s explicit team allocation. Explain substantial AI assistance honestly using the cumulative AI log. Each member should answer questions about their work.
The following three slides are backup material. Use them only when relevant.
Before evaluation, have the submitted Devpost project link ready separately. The team has not supplied that link in this conversation. Do not claim that the GitHub or Hugging Face link replaces it.

Sources:
https://github.com/waleedirfan2006-arch/Heat-Shift-/blob/main/TEAM_CONTRIBUTIONS.md
https://github.com/waleedirfan2006-arch/Heat-Shift-/blob/main/AI_Use_Log.md

## Slide 10: Backup: errors by group and uncertainty

BACKUP ONLY
All scores use mean absolute error in Celsius. January is the group where the model loses to persistence. March calibration uses 183 Karachi, 398 Lahore and 174 Multan examples, separate from the Jan-Feb validation. Calibration coverage is approximately 90% on the calibration rows themselves. It is not independent future coverage. Time dependence limits a simple coverage interpretation.
Do not read the chart/table as percent accuracy.

Sources:
https://github.com/waleedirfan2006-arch/Heat-Shift-/blob/main/evidence/final_audit/primary_model/metrics.json

## Slide 11: Backup: effort, speed and memory

BACKUP ONLY
These are context-specific benchmarks, not service-level guarantees. The quality and insight values are medians over five warm runs on 5,012 Karachi rows. Traced Python allocation peaks were 2,933,053 and 1,970,584 bytes, excluding native allocations. Original training peak memory and training speed were not verified. The exported model JSON is about 0.74 MiB. Browser startup and external requests dominate first use.
Educational outcomes include source receipts, time-based splits, baseline comparison, uncertainty, citation checks and honest refusals.

Sources:
https://github.com/waleedirfan2006-arch/Heat-Shift-/blob/main/OPTIMIZATION_LOG.md
https://github.com/waleedirfan2006-arch/Heat-Shift-/blob/main/evidence/final_audit/agent_benchmarks.json
https://github.com/waleedirfan2006-arch/Heat-Shift-/blob/main/AI_Use_Log.md

## Slide 12: Backup: project links and evidence

BACKUP ONLY
Primary source documentation and project records are linked below. The exact original Open-Meteo collection URL/model/fetch time and original JMA fitting-feature/search records remain incomplete. Fresh archive receipts prove the audit reproduction, not the original data arrival.
Submission reminder: the latest organizer notice requires slides, project demonstration and the submitted Devpost link. Every team member must attend and understand their part. This deck provides approximately six minutes of presentation/demo plus four minutes of questions. Check team slot and reporting time separately.
AI disclosure: Codex substantially assisted with integration, evaluation, automation and documents. User-reported team roles remain distinct from file-by-file authorship verification.

Sources:
https://www.ncei.noaa.gov/products/land-based-station/integrated-surface-database
https://open-meteo.com/en/docs/previous-runs-api
https://aviationweather.gov/data/api/
https://github.com/waleedirfan2006-arch/Heat-Shift-/blob/main/AI_Use_Log.md
https://github.com/waleedirfan2006-arch/Heat-Shift-/blob/main/TEAM_CONTRIBUTIONS.md