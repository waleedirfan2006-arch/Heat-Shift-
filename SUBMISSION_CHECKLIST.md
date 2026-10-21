# Final submission checklist — 21 October 2026

Deadline: **12:00 AM Thursday 22 October PKT (midnight after Wednesday)**. This is an evidence audit, not a claim of full eligibility.

- [x] **Warehouse — verified:** Clean-start snapshot restoration and 14 checks; make data also passed on Ubuntu Actions.
- [ ] **Manifest — partial:** Every raw file listed with SHA/source/query/fetch/license fields; original metadata for three Open-Meteo snapshots remains unverified.
- [x] **Quality agent — verified:** Original source fingerprint preserved; fix/fill/flag and quality_log available.
- [x] **Baseline before results — verified:** Contract committed 19 Oct 14:05:30 UTC, before Ridge results at 16:18:40 UTC and later JMA artifact.
- [x] **Model beats baseline — verified_with_limits:** Reused validation MAE 1.101946 vs 1.235165 C; January loses; bootstrap interval includes zero.
- [x] **Uncertainty groups — verified_with_limits:** City/month errors and nominal March 90% calibration bands; future coverage unproven.
- [x] **Insight grounding — verified:** Strict whole-request scope; gold-table SHA256, original row IDs and computed numeric claims; sourced guidance and unsupported refusals.
- [ ] **Hourly pipeline — partial:** Minute-17 schedule configured; real push runs passed. This does not prove the requested historical hourly window or Prefect execution.
- [x] **Space — verified:** Public Space shows freshness, quality status and last successful run. Original Python agents executed in browser.
- [ ] **Prefect export — missing:** No unedited prefect_runs.csv for 20 Oct 16:00 to 21 Oct 16:00 PKT found across fourteen branches.
- [ ] **Prefect screenshot — missing:** No actual Prefect dashboard screenshot found. GitHub Actions evidence is not a substitute.
- [ ] **Declaration deadline — unmet:** First Dataset_Declaration_DRAFT.md commit 19 Oct 18:46:43 UTC / 23:46:43 PKT, after Monday noon.
- [x] **Summary — verified:** Summary.pdf exactly one page; team roles and known gaps included.
- [x] **Demo — verified_with_limits:** Public captioned dashboard walkthrough below 180 seconds; screenshot sequence, no audio or continuous live screen recording.
- [x] **Ai log — verified:** Cumulative AI assistance log updated; no invented human sign-off.
- [x] **Business optimization — verified:** User/payer/value/cost hypotheses, measured accuracy/speed/limited memory, unknown effort labelled.
- [x] **Slides — verified:** Editable PowerPoint, PDF backup and notes supplied; latest event notice requires slides.
- [ ] **Devpost — human_action:** Submission/link not provided or verified; prepare it before presentation.
- [ ] **Physical viva — human_action:** All members must attend, rehearse and explain their work.
- [ ] **Final tag — release_workflow:** Final tag must match reviewed main after all files; verify successful finalization workflow. Operational status uses separate branch.

## Historical evidence cannot be recreated

No Prefect export or screenshot was located on main or thirteen other branches. Do not rename GitHub Actions logs as Prefect runs, fabricate a screenshot, edit an export or backdate a declaration. The late draft and missing history require an organizer decision if exceptions are possible; this software audit cannot grant one. No message has been sent to organizers.

The baseline contract predates committed results, but that does not prove a timely dataset declaration. Dataset proposal PDF is a current source disclosure, not a replacement for the missed deadline.

## Rehearse and submit

The latest notice requires slides, a demonstration and a Devpost link. Use submission/HeatShift_Presentation.pptx and its PDF backup. Aim for six minutes presenting and four for questions within the ten-minute slot. The demo guideline is: 0:00–0:30 problem/user/decision; 0:30–1:15 sources/quality; 1:15–2:15 dashboard/baseline/citation/refusal; 2:15–3:00 group errors/limits/Pakistani impact. The saved video is captioned; record your own voice if desired.

Waleed Irfan: model development/improvement. Syed Mateen Ali: developed, managed and maintained both agents. Aman Khan Lodhi: data cleaning, warehouse management and preparation. Roles are team-reported; substantial AI help is separately disclosed. Every member must attend and understand the entire approach. Reporting times depend on team group; first twenty teams report by 8:30 AM, remaining teams from 1 PM. Confirm your assigned slot in the official channel.

Final code stays on the v1.0-final commit. Real operational refreshes write only the heatshift-runtime branch. Check the finalization workflow and tag target after publication; do not push further source changes once frozen.
