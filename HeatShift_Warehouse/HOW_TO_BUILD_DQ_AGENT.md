# Build the Data Quality Agent — Recommended instructions

Status: NOT BUILT in this package, as requested.
The current script has ordinary cleaning checks. These are useful building blocks, not the finished agent.
Suggested owner: student A. Student B connects it to the pipeline. Student C checks explanations.

## What it is

The agent is a program that asks a checking tool to inspect data. It then chooses a safe action and explains why.
Recommended simplest design: Python + Pandera + a small decision table. Pandera is a tool for checking table columns and values.
A chatbot is not needed for these decisions. A fixed decision table is easier to test and explain.

## The five parts to build

| Part | Job | Suggested future file |
|---|---|---|
| Validation tool | Test table structure, types, keys, ranges and missing values. | validation_tools.py |
| Decision function | Choose FIX, FLAG or QUARANTINE for each finding. | dq_agent.py |
| Action function | Apply only approved safe changes to a copy. | dq_actions.py |
| Evidence writer | Save the reason, affected rows, count and timestamp. | dq_decisions.csv |
| Gate controller | Allow the next stage only after its checks pass. | pipeline.py integration |

A gate means a checkpoint. Quarantine means put a bad record aside for review, with its original data and reason.
Do not create these filenames and claim they work until their logic is implemented and tested.

## Work in this order

1. Install Pandera in a separate project environment. Record the installed version in requirements.txt after testing it.
2. Define required columns and types. Use strings for station IDs, dates for timestamps and numbers for temperatures.
3. Run Pandera with all-error reporting. Collect every failure, rather than stopping at the first bad row.
4. Send failures to the decision function. Do not let a language model invent corrections.
5. Apply the safe action to a working copy. Never change 00_raw.
6. Save the decision log and the affected record IDs.
7. Run the checks again. Publish accepted data only if the gate passes.
8. If a critical check fails, keep the last good warehouse and dashboard. Write a failure status and alert for the operator.

## Decision table

These are Recommended rules, not measured new findings.

| Finding | Decision | Explanation |
|---|---|---|
| NOAA encoded temperature with known format | FIX | Decode the documented tenths of a degree to Celsius. |
| Same station/time has repeated accepted reports | FIX + FLAG conflicts | Use the documented quality/report priority; keep alternatives and flag conflicting temperatures. |
| Missing current temperature | QUARANTINE from prediction examples | The model and baseline both need the current measurement. |
| Missing measured target | QUARANTINE from training/scoring examples | Never invent tomorrow's measured answer. This is normal for the newest live records. |
| Missing older optional input | FLAG | Keep blank. During model preparation only, use a replacement learned on training data and mark it. |
| Invalid time, station or critical column | QUARANTINE / stop gate | The program cannot safely identify the observation. |
| Temperature rejected by quality rules | QUARANTINE | Keep raw evidence; do not treat it as a trusted measurement. |
| Known sparse reporting interval | FLAG | Empty hourly slots are not automatically a sensor failure. |
| Unexpected source delay | FLAG and hold affected output | Show old data honestly; never relabel it as current. |
| New data look different from training | FLAG for review | Do not automatically delete unusual but real hot weather. |

The guide permits filling where justified; this project does not need to fill station targets. A decision to flag instead of fill is valid and must be explained.

## Two gates from the poster

**Gate 1, before cleaned data:** required columns, valid types, station/time keys, repeats and source-based ranges.

**Gate 2, before final data:** missing required values, exact-time joins, time order, source freshness and drift.
Drift means new data no longer look like training data.
Recommended first drift check: save temperature ranges by city and calendar month from training only. Compare a later replay batch with its matching training group. Choose and record a warning threshold before running the demo; test whether normal seasons trigger too many warnings. Do not use the locked test to choose that threshold.

For replay, compare event times with the historical replay clock. Separately show the real wall-clock fetch/run time. An old NOAA event is expected in replay and must never be presented as today's weather.

## What one log row needs

run_id, gate, source_file, record_ids, field, rule_id, finding, decision, reason, affected_count, before_value, after_value, is_imputed, timestamp_utc, status.

`is_imputed` means the value was estimated instead of directly observed. Set it only when a value was actually filled.
Use actual counts from the tool result. Keep human approvals in a separate approval log with approver, time and action.

## How to connect it

Recommended logic:

1. Restore or fetch raw data and check file fingerprints.
2. Ask the agent to run Gate 1.
3. Apply logged safe fixes; retain rejected records separately.
4. Build the cleaned tables.
5. Ask the agent to run Gate 2.
6. Build final tables only for accepted data.
7. Replace the published database only after all required checks pass.
8. Return the real status and last successful run to the dashboard.

The existing builder already stages results before publication. It needs this explicit agent integration; renaming build_warehouse.py to dq_agent.py is not enough.

## Tests before calling the agent complete

- [ ] A valid small sample passes.
- [ ] A malformed date is quarantined and explained.
- [ ] A duplicate/conflict uses the stated rule and preserves alternatives.
- [ ] A missing target stays missing and is excluded from scoring.
- [ ] A source delay is shown using the correct replay/live clock.
- [ ] A critical failure leaves the last good warehouse unchanged.
- [ ] Log counts match the affected record IDs.
- [ ] A second identical run does not duplicate records.
- [ ] The team can explain each decision without asking the AI.

Use copies of real rows for ordinary checks. If you deliberately corrupt a copy, label it a synthetic stress test. Never use those corrupted examples to measure the predictive model's accuracy.

Official tool documentation: https://pandera.readthedocs.io/en/stable/
