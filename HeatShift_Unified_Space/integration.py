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
from insight_policy import classify

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
        decision = classify(question, city)
        # Verify the actual canonical table bytes before allowing numeric answers.
        gold = json.loads((ROOT / "gold_manifest.json").read_text(encoding="utf-8"))[city]
        gold_path = ROOT / "evidence" / gold["file"]
        if not gold_path.exists():
            gold_path = ROOT / gold["file"]
        if hashlib.sha256(gold_path.read_bytes()).hexdigest() != gold["sha256"]:
            raise ValueError("Gold table fingerprint mismatch. No insight produced.")
        agent.report_dir = base
        agent.retriever = None
        agent.data_store = None
        if decision["intent"] == "refuse":
            agent.processed_dir = base / "no_supported_evidence"
            agent.docs_dir = base / "no_supported_documents"
            result = agent.ask(question)
            result["answer"]["answer"] = "I don't know. " + decision["reason"]
        elif decision["intent"] == "statistics":
            # Numbers come only from the gold table, not unrelated retrieved prose.
            agent.docs_dir = base / "no_document_numbers"
            result = agent.ask(question)
            result["answer"]["answer"] = result["answer"]["answer"].split(" This is information,")[0]
        else:
            # Retrieve with Mateen's original retriever, then require the intended section.
            query = decision["section"]
            documents = agent.retrieve_documents(query, limit=20)
            documents = [d for d in documents if d["row_id"] == "section:" + query]
            if not documents:
                result = {"question":question,"answer":{"answer":"I don't know. The requested trusted source is unavailable.","supported":False,"citations":[]},"citations_valid":True}
            else:
                # Return the complete trusted section. No invented numeric advice.
                sections = re.split(r"(?m)^# ", guide.read_text(encoding="utf-8"))
                section = next(x for x in sections if x.partition("\n")[0].strip() == query)
                result = {"question":question,"answer":{"answer":section.partition("\n")[2].strip(),"supported":True,"citations":[{"source":guide.name,"row_id":"section:"+query,"source_sha256":hashlib.sha256(guide.read_bytes()).hexdigest()}]},"citations_valid":True}
        result["policy"] = {"version":"strict-scope-v2","intent":decision["intent"],"primary_user":"Everyday weather planner","recommendations":"Only sourced data-use guidance; no personalized safety advice"}
        result["gold_table"] = gold
        result["numeric_claims"] = []
        result["evidence_rows"] = []
        if decision["intent"] == "statistics" and result["answer"]["supported"]:
            series = frame["temperature_c"]
            for metric, value in [("minimum",float(series.min())),("maximum",float(series.max())),("mean",float(series.mean())),("count",int(series.count()))]:
                result["numeric_claims"].append({"metric":metric,"column":"temperature_c","value":value,"gold_table":gold["file"],"gold_sha256":gold["sha256"],"row_id":city.lower()+":aggregate"})
            for pos in sorted({int(series.idxmin()),int(series.idxmax())}):
                row = frame.iloc[pos]
                result["evidence_rows"].append({"row_position":pos,"gold_row_id":row["source_row_id"],"time":row["time"],"temperature_c":float(row["temperature_c"]),"gold_table":gold["file"]})
            for c in result["answer"]["citations"]:
                suffix = c["row_id"].rsplit(":",1)[-1]
                c["source"] = gold["file"]
                c["source_sha256"] = gold["sha256"]
                c["gold_row_id"] = city.lower()+":aggregate" if suffix == "aggregate" else frame.iloc[int(suffix)]["source_row_id"]
                c["row_id"] = gold["file"]+":"+suffix
            result["citations_valid"] = all(c["source_sha256"] == gold["sha256"] for c in result["answer"]["citations"])
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
