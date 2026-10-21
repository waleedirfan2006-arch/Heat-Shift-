---
title: HeatShift Weather Dashboard
emoji: ☀️
colorFrom: green
colorTo: yellow
sdk: static
app_file: index.html
---

# Responsive HeatShift dashboard

Live: https://huggingface.co/spaces/Waleed-1234/HeatShift-Dashboard

This is the source of the deployed dashboard. It contains Waleed's frozen model export and byte-identical copies of Mateen's agents. `integration.py` is an adapter; it checks agent fingerprints, isolates temporary files, normalizes explicitly zoned timestamps and adds trusted project-document retrieval. Vendor agent rules are unchanged.

Run `python download_runtime.py` once to download the official pinned browser Python runtime and pandas dependencies. Then serve this folder through a static HTTP server, or upload its contents to a free Hugging Face Static Space. Runtime wheels and WebAssembly assets are already deployed on the live Space; they are generated dependencies and are not duplicated in this GitHub folder.

CSV uploads and agent execution remain in the browser. First agent use downloads Python and pandas. The Insight Agent is lightweight, deterministic retrieval plus numeric summarization with citations, not a general LLM chatbot. A strict full-question policy permits whole-table historical summaries and selected sourced guidance. Unsupported cities, time filters, future weather, pollution, personal recommendations and unknown wording receive I do not know. Gold-table hashes and original source row IDs are recorded.

The dashboard requests latest hourly status from the public GitHub `runtime/latest.json` on the separate `heatshift-runtime` branch. Stale or unavailable snapshots are labelled. The trained model is never automatically retrained by the hourly workflow.
