# HackInsight 26 final delivery checklist

Audit date: 21 October 2026. This maps only the organizer message supplied by Waleed.

| Requirement | Status and evidence |
|---|---|
| Raw / cleaned / processed warehouse, manifest.csv, make data | Added root Makefile; rebuild passed 14 checks locally and the same command passed on GitHub Ubuntu. Original data preserved. |
| Data Quality Agent + fix/fill/flag quality_log | Original Mateen source fingerprint preserved; browser and hourly adapters run it. Root quality_log.json and run artifacts contain real decisions. |
| Model beats declared baseline | Reproduced aggregate validation win 1.102 vs 1.235 C on 1,783 identical rows. January loses; bootstrap interval includes zero. Reused validation, not an independent final-test guarantee. |
| Uncertainty and errors by group | City/month metrics and March-calibrated nominal 90% bands with row IDs in evidence/final_audit/primary_model/. |
| Insight Agent RAG, citations, row IDs, refusal | Original agent with trusted Markdown section retrieval and numeric training-table summaries. Deterministic lightweight RAG; no general LLM. Unsupported AQI and unrelated requests refused. |
| Automated hourly pipeline | .github/workflows/hourly.yml, minute 17 UTC hourly; first push-triggered run [39608434792](https://github.com/waleedirfan2006-arch/Heat-Shift-/actions/runs/39608434792) succeeded. A successful push run does not prove an hourly cron event has fired yet. Delays possible. |
| Hugging Face Space | [Public dashboard](https://huggingface.co/spaces/Waleed-1234/HeatShift-Dashboard). Live forecast and preserved-agent execution checked. |
| datasetpropsal.pdf | submission/datasetpropsal.pdf, exact requested spelling, source roles and gaps included. |
| GitHub v1.0-final | Final release/tag published after the submission files; verify the Releases link. |
| One-page Summary.pdf | submission/Summary.pdf, page count verified as one. |
| Demo <=3 minutes, no login | submission/HeatShift_Demo.mp4, captioned walkthrough of actual dashboard screenshots; no narration. Public GitHub release/repository download. |
| AI_Use_Log.md | Root cumulative log appended; substantial AI assistance declared. No invented human sign-off. |
| Physical viva, all members | HUMAN ACTION REQUIRED: team must attend and understand their own work. |
| Business model and impact | Business_Model.md and submission/Business_Model.pdf; hypotheses and unmeasured impact clearly labelled. |
| Optimization: effort, accuracy, speed, memory | OPTIMIZATION_LOG.md and viva guide. Unknown original training memory/human hours remain unknown. |

## Items software cannot honestly complete

1. Every team member must attend the physical viva and review the final claims, code, AI log and their own contribution.
2. Recover original Open-Meteo request/model/fetch receipts and original JMA training feature/search records from the people who collected/trained them. The audit cannot invent these.
3. Independent future-season proof, total browser memory, actual business demand/costs and measured social impact are not established. Do not claim them as completed.
4. The provided organizer message does not explicitly require a slide deck. The three-page viva guide includes a speaking outline. Check any separate event announcement for extra requirements.

Read submission/Project_Explanation_Viva.pdf first for tomorrow's explanation.
