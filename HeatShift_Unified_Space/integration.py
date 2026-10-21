"""Read-only integration of Mateen's unchanged agents and the forecast UI."""
from __future__ import annotations

import gzip
import hashlib
import importlib.util
import json
import re
import tempfile
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent
CITIES = ("Karachi", "Lahore", "Multan")


def _load_agent(filename, class_name):
    path = ROOT / "vendor" / filename
    if not path.exists():
        path = ROOT / filename
    manifest = ROOT / "evidence/integration_provenance.json"
    if not manifest.exists():
        manifest = ROOT / "integration_provenance.json"
    expected = json.loads(manifest.read_text(encoding="utf-8"))["agents"][filename]
    if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
        raise ValueError("Agent source changed. Review the integration before running it.")
    spec = importlib.util.spec_from_file_location("heatshift_" + path.stem, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return getattr(module, class_name)


def training_evidence(city):
    if city not in CITIES:
        raise ValueError("Choose a supported city.")
    path = ROOT / "evidence" / f"{city.lower()}_train.csv.gz"
    if not path.exists():
        path = ROOT / f"{city.lower()}_train.csv.gz"
    return pd.read_csv(path)


def run_quality(data: bytes, filename: str):
    """Keep all agent writes in a disposable folder; never touch model inputs."""
    if len(data) > 10 * 1024 * 1024:
        raise ValueError("Use a CSV smaller than 10 MB.")
    name = re.split(r"[/\\]", filename)[-1]
    if not name.lower().endswith(".csv") or name in (".csv", ""):
        raise ValueError("Upload a CSV file.")
    agent_class = _load_agent("data_quality_agent.py", "DataQualityAgent")
    with tempfile.TemporaryDirectory(prefix="heatshift_quality_") as folder:
        base = Path(folder)
        source_dir = base / "uploaded"
        source_dir.mkdir()
        source = source_dir / name
        source.write_bytes(data)
        # Original constructors hard-code project folders with different case.
        # Configure an instance without changing vendor source or writing there.
        agent = agent_class.__new__(agent_class)
        agent.project_dir = base
        agent.input_dir = source_dir
        agent.output_dir = base / "processed"
        agent.output_dir.mkdir()
        notes = []
        # The unchanged agent subtracts a naive clock from the final timestamp.
        # Normalize only explicitly zoned dates to UTC in the isolated copy.
        preview = agent._read_csv(source)
        for column in preview.columns:
            if column.lower().strip() in ("time", "date", "datetime", "timestamp"):
                parsed = pd.to_datetime(preview[column], errors="coerce")
                if isinstance(parsed.dtype, pd.DatetimeTZDtype):
                    preview[column] = parsed.dt.tz_convert("UTC").dt.tz_localize(None)
                    payload = preview.to_csv(index=False)
                    if "open-meteo" in name.lower():
                        payload = "\n\n\n" + payload
                    source.write_text(payload, encoding="utf-8")
                    notes.append(f"Adapter converted explicitly zoned {column} to UTC without a suffix in the temporary copy. Display these times as UTC. The agent's generic time-zone flag still appears unchanged.")
        report = agent.process_file(source)
        cleaned = Path(report["output"]).read_bytes()
        report["source"] = name
        report["output"] = Path(report["output"]).name
        report["input_sha256"] = hashlib.sha256(data).hexdigest()
        report["integration_notes"] = notes
        # Agent's naive local clock makes age unreliable across server zones.
        report["data_age_hours"] = None
        report["integration_notes"].append("Data age is not asserted: the original agent uses a server-local clock without time-zone information.")
        return report, cleaned


def ask_insight(city, question):
    """Run the original agent on one city's training observations only."""
    frame = training_evidence(city)
    agent_class = _load_agent("insight_agent.py", "InsightAgent")
    with tempfile.TemporaryDirectory(prefix="heatshift_insight_") as folder:
        base = Path(folder)
        source = base / f"{city.lower()}_training_cleaned.csv"
        frame.to_csv(source, index=False)
        agent = agent_class.__new__(agent_class)
        agent.project_dir = base
        agent.processed_dir = base
        agent.docs_dir = base / "docs"
        agent.docs_dir.mkdir()
        guide = ROOT / "trusted_weather_guide.md"
        if guide.exists():
            (agent.docs_dir / guide.name).write_text(guide.read_text(encoding="utf-8"), encoding="utf-8")
        # Domain guard invokes the original refusal path instead of inventing an answer.
        supported_terms = r"\b(temperature|temperatures|temp|weather|minimum|maximum|average|mean|summary|summarize|recorded|data|aqi|pollution|pollutant|uncertainty|baseline|station|quality|interpolation|forecast|citations)\b"
        if not re.search(supported_terms, question, flags=re.I):
            agent.processed_dir = base / "no_supported_evidence"
        agent.report_dir = base
        agent.retriever = None
        agent.data_store = None
        result = agent.ask(question)
        # Keep citation row numbers unchanged; shorten disposable file paths.
        for item in result["answer"]["citations"]:
            item["source"] = Path(item["source"]).name
        result["scope"] = f"{city}: training observations only; historical, not live."
        result["data_start_utc"] = frame["time"].min()
        result["data_end_utc"] = frame["time"].max()
        result["rows"] = len(frame)
        return result


def forecast_html():
    """Bundle existing JS/CSS/data into one iframe without changing inference."""
    folder = ROOT / "prediction"
    html = (folder / "index.html").read_text(encoding="utf-8")
    html = html.replace('<link rel="stylesheet" href="style.css">',
                        '<style>' + (folder / "style.css").read_text(encoding="utf-8") + '</style>')
    assets = {}
    for name in ("model.json", "station_weather_model.json", "experiment.json", "weather_model_metrics.json"):
        path = folder / name
        assets[name] = json.loads(gzip.decompress(path.with_suffix(path.suffix + ".gz").read_bytes())) if name in ("model.json", "station_weather_model.json") else json.loads(path.read_text(encoding="utf-8"))
    assets["station_weather_model.json.gz"] = assets.pop("station_weather_model.json")
    bootstrap = "const bundledAssets=" + json.dumps(assets).replace("<", "\\u003c") + ";\n"
    bootstrap += "const nativeFetch=window.fetch.bind(window); function bundledFetch(url,options){return Object.prototype.hasOwnProperty.call(bundledAssets,url)?Promise.resolve(new Response(JSON.stringify(bundledAssets[url]),{headers:{'Content-Type':'application/json'}})):nativeFetch(url,options);}\n"
    for name in ("model.js", "core.js", "app.js"):
        code = (folder / name).read_text(encoding="utf-8")
        if name == "app.js":
            code = bootstrap + code.replace("fetch(", "bundledFetch(")
        html = html.replace(f'<script src="{name}"></script>', "<script>" + code.replace("</script", "<\\/script") + "</script>")
    return html
