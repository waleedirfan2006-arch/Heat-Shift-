# Audit update — read first

This update completes the available-data quality/leakage review and adds protective checks.
Open-Meteo original collection evidence is still incomplete. Do not mark it verified.

## Files to read

1. `HeatShift_Warehouse/audit/DATA_QUALITY_AND_LEAKAGE_REVIEW.md`: findings, limitations, test evidence and team handoff.
2. `HeatShift_Warehouse/audit/OPEN_METEO_PROVENANCE.md`: verified facts and exact steps to recover missing evidence.
3. `HeatShift_Warehouse/audit/OPEN_METEO_EVIDENCE_TO_COMPLETE.csv`: collector evidence form.
4. `HeatShift_Warehouse/audit/audit_results.json`: actual audit result and input fingerprints.
5. `AI_Use_Log.md` and `HeatShift_Warehouse/AI_Use_Log.md`: AI contribution record and pending human review.

The new `validate_data.py` must stay beside `train_model.py`. It is required by the updated training script.
The model choices and saved model are unchanged. No training or scoring was performed.

## Exact local verification (Git Bash, repository root)

Recommended: Python 3.12 installed. `py --version` shows the selected Python version.

```bash
cd /d/Heat-Shift-
py -3.12 -m venv .venv-audit
.venv-audit/Scripts/python.exe -m pip install -r HeatShift_Warehouse/requirements.txt -r HeatShift_Training/requirements.txt
.venv-audit/Scripts/python.exe HeatShift_Warehouse/audit_data.py
.venv-audit/Scripts/python.exe HeatShift_Training/test_data_guards.py
```

Expected: 211 checks pass with documented limitations; 10 guard tests pass. If any command fails, stop and share the error. Do not change original hashes to make a failure disappear. `.venv-audit` is ignored by Git.
For a fresh warehouse rebuild, use a new destination outside the repository:

```bash
.venv-audit/Scripts/python.exe HeatShift_Warehouse/pipeline.py --output ../HeatShift_Audit_Rebuild
```

If a raw hash mismatch occurs on an existing Windows checkout, first preserve the file and inspect whether Git changed line endings. Do not delete originals or edit the manifest to hide the mismatch. The snapshot ZIP retains the expected bytes. New `.gitattributes` prevents further raw conversion.

## Remaining evidence action

Ask the original Open-Meteo downloader for the download URL and dated record via Ctrl+J, or the original collection script/log. Fill the supplied evidence form. If unavailable, request organiser acceptance or an explicitly permitted new collection. A new download cannot establish the old download time.

## Publication

The assistant prepared branch `audit-data-provenance-20261020` from base `ffdecac`.
The final chat response states whether push succeeded. This file does not imply a successful push or merge.
