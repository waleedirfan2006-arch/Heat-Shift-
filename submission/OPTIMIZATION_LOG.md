# Optimization and evaluation log

All lower MAE values are better; values are C, not percentage accuracy. These entries preserve both successes and failures.

| Change / experiment | Accuracy result | Speed / memory evidence | Decision |
|---|---|---|---|
| Original Ridge change prediction | MAE 1.320762 vs persistence 1.235165 on 1,783 validation rows | Not recorded | Did not beat baseline; retained for learning |
| Station-only HGB 250/7 alternative (earlier run) | MAE 1.237479 vs 1.235165 | Original fitting runtime/peak memory not verified | Not promoted |
| Existing JMA-assisted HGB 300/15, independently reproduced 21 Oct | MAE 1.101946 vs raw baseline 1.235165; January worse | 80.3972 ms / 2,538 warm Node rows; heap snapshot 11,503,288 bytes | Keep frozen model; no parameter change |
| Separate March city calibration | Nominal 90% bands +/-2.224, 3.084, 2.271 C; no forecast point-score change | 755 residuals; independent future coverage not measured | Replace training-error display with labelled calibration ranges |
| Static browser inference + original Python agents via Pyodide | No change to model parameters or agent fingerprints | About 25 MB first-use runtime download; first agent startup can take about a minute | Enables existing free static Space; first-use overhead remains |
| Local quality/insight benchmarks on Karachi 5,012 rows, five warm repetitions | No new predictive accuracy | Median 0.238170 / 0.103272 s; traced Python peaks 2,933,053 / 1,970,584 bytes | Record reproducible context; not total process/browser memory |
| Hourly combined METAR fetch + three JMA requests | No fitting; marks failures explicitly | Successful manual run 2.777 s; one sample is not an SLA | Schedule hourly; retain evidence |

Evidence: evidence/final_audit/primary_model/metrics.json, agent_benchmarks.json and hourly_manual_run/. The model heap snapshot excludes startup/network, loading and native/process memory; Python allocation tracing excludes native arrays. No original training speed, total browser memory, energy use or human hours were recorded. The 7-day bootstrap improvement interval [-0.0417, 0.2707] includes zero. Locked-test/replay/reserve were not scored in the final audit.


## Final scope and publication changes

| Change | Gain | Cost / measurement limit |
|---|---|---|
| Strict whole-request scope and table fingerprints | Prevents unsupported city/date/future/advice answers being inferred from unrelated statistics; stores numeric lineage | Conservative grammar refuses arbitrary paraphrases. Additional hash/policy overhead not benchmarked; old agent timings do not measure this version. |
| Separate runtime branch and preserved last-success pointer | Hourly observations can refresh while final source tag stays frozen; failures remain visible | Still depends on scheduled Actions and upstream weather APIs; no uptime guarantee or historical Prefect proof. |
| Clean-start snapshot restore and raw-hash checks | Deterministic warehouse rebuild; changed inputs fail rather than silently repair evidence | Packaged snapshots cannot recover missing original collection metadata. |

No model parameters were changed in this audit. Human hours and original training memory remain unrecorded. No claim of improved prediction accuracy is attached to UI or policy changes.
