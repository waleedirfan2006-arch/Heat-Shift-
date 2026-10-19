# Add this update to your existing repository

Your reported setup:
- Repository: https://github.com/waleedirfan2006-arch/Heat-Shift-
- Local project: D:\Heat-Shift-
- Warehouse: D:\Heat-Shift-\HeatShift_Warehouse
- Earlier dataset commit: 8f3e9f1; branch add-heatshift-dataset; PR #1 merged to main.
- Local main matches origin/main and is clean, as reported by you.

That upload contained the earlier 42-file package. This revised package adds NOAA 2022, source evidence, manifest.csv, snapshot recovery, the AI log and next-stage instructions. The assistant has not pushed this update to your repository.

## 1. Make a new branch

Recommended commands in PowerShell:

```powershell
cd D:\Heat-Shift-
git status
git switch main
git pull --ff-only
git switch -c complete-warehouse-docs
```

If git status shows work you have not saved, preserve it before switching. If the suggested branch name already exists, use another new name rather than deleting it.

## 2. Copy the updated files

1. Download and extract the updated HeatShift_Warehouse.zip into a temporary folder outside the repository.
2. Open the extracted HeatShift_Warehouse folder.
3. Copy its CONTENTS into D:\Heat-Shift-\HeatShift_Warehouse. Compare and replace older package files, while preserving any additional work your team made.
4. Do not create D:\Heat-Shift-\HeatShift_Warehouse\HeatShift_Warehouse.
5. Keep warehouse.sqlite ignored by Git. It is generated locally by the rebuild command.
6. Keep source_snapshots.zip, manifest.csv and manifest.json tracked. The snapshot archive is needed for the offline clean-start rebuild. Do not ignore all ZIP files.
7. Copy AI_Use_Log.md to the repository root too, because the guide requests it as a submission file. If a root log already has team entries, merge the new entries instead of overwriting them. Maintain the root copy as the submission log.

## 3. Preserve your ignore rules

Keep the existing .gitignore. Add these patterns only if not already covered:

```gitignore
**/warehouse.sqlite
**/warehouse.sqlite.next
**/warehouse_build.lock
**/__pycache__/
**/fresh_build/
**/new_fetch_checks/
**/*.next
```

Do not force-add the large SQLite file. Rebuilding it locally is the intended workflow.

## 4. Rebuild and inspect

```powershell
cd D:\Heat-Shift-\HeatShift_Warehouse
py -m pip install -r requirements.txt
py pipeline.py --output fresh_build
```

Use python instead of py if that is your installed command. Python 3.12 is the tested version.
The destination fresh_build should be new for your first clean-start check. The build restores raw snapshots, verifies fingerprints and rebuilds the tables/database.

Expected current counts: 15 raw files; 122,839 source rows; 16,463 training examples; 5,346 locked-test examples. These are data counts, not model accuracy.
Read the real quality summary and rebuild receipt. A successful rebuild is not a full data-quality audit or leakage assessment.

## 5. Review, commit and push

```powershell
cd D:\Heat-Shift-
git status
git check-ignore HeatShift_Warehouse/warehouse.sqlite
git add .gitignore HeatShift_Warehouse AI_Use_Log.md
git diff --cached --stat
git commit -m "Complete warehouse rebuild and document data provenance and AI assistance"
git push -u origin complete-warehouse-docs
```

Run git add only after copying the root AI log. Review the staged files: warehouse.sqlite and fresh_build must not be included. If git check-ignore prints nothing, review the ignore rule before committing. Do not use force-add or force-push.
Create a pull request, review the changes and merge when your team is ready. Keep the original commit and source history.

## 6. Actual next technical work

Data Quality Agent remains intentionally unbuilt. A full data-quality audit, leakage assessment and model-readiness review remain pending, followed by model training. Use HOW_TO_BUILD_DQ_AGENT.md and REMAINING_STEPS.md.
Start the real hourly scheduling setup in parallel. The evidence window starts Tuesday 20 October at 4 PM PKT and ends Wednesday 21 October at 4 PM PKT.

The earlier dataset upload does not by itself prove a Dataset Declaration was committed before noon. Check the actual declaration file and its commit history; never backdate the new draft.
