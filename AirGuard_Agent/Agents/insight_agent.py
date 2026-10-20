from pathlib import Path
from typing import Any
from datetime import datetime
import json
import re

import pandas as pd

POLLUTANT_TERMS = (
    "pollution", "pollutant", "pm2.5", "pm25", "pm10", "aqi",
    "air quality", "ozone", "no2", "so2", "co",
)
POLLUTANT_COLUMN_HINTS = (
    "pm2.5", "pm25", "pm2_5", "pm10", "aqi", "ozone", "no2", "so2",
    "carbon_monoxide",
)
POLLUTANT_EXACT = {"co", "o3"}


class InsightAgent:
    """Evidence-first insight helper for AirGuard.

    Rules: every number comes from the cleaned table by code (no LLM numbers),
    every claim carries a citation, and unsupported questions get "I don't know".
    """

    def __init__(self, retriever: Any = None, data_store: Any = None):
        self.retriever = retriever
        self.data_store = data_store

        self.project_dir = Path(__file__).resolve().parent.parent
        self.processed_dir = self.project_dir / "data" / "processed"
        self.docs_dir = self.project_dir / "docs"  # trusted guidance (.md / .txt)
        self.report_dir = self.processed_dir
        self.report_dir.mkdir(parents=True, exist_ok=True)

    # ---------- evidence from tables ----------
    def _summarise_file(self, path: Path) -> list[dict]:
        """One aggregate record plus the min/max rows it points to."""
        frame = pd.read_csv(path)
        aggregate: dict = {}
        wanted_rows: set[int] = set()

        for column in frame.select_dtypes(include="number").columns:
            series = frame[column].dropna()
            if series.empty:
                continue
            low, high = int(series.idxmin()), int(series.idxmax())
            aggregate[column] = {
                "min": float(series.min()), "max": float(series.max()),
                "mean": float(series.mean()), "count": int(series.size),
                "min_row": low, "max_row": high,
            }
            wanted_rows.update((low, high))

        if not aggregate:
            return []

        items = [{
            "source": str(path),
            "row_id": f"{path.name}:aggregate",
            "data": aggregate,
        }]
        for row_number in sorted(wanted_rows):
            row = frame.loc[row_number]
            items.append({
                "source": str(path),
                "row_id": f"{path.name}:{row_number}",
                "data": row.where(pd.notna(row), None).to_dict(),
            })
        return items

    def retrieve_evidence(self, question: str) -> list[dict]:
        evidence = []

        if self.retriever is not None:
            result = self.retriever(question)
            if isinstance(result, list):
                evidence.extend(result)

        if self.data_store is not None:
            if callable(self.data_store):
                result = self.data_store(question)
            elif hasattr(self.data_store, "retrieve"):
                result = self.data_store.retrieve(question)
            else:
                result = []
            if isinstance(result, list):
                evidence.extend(result)

        if not evidence and self.processed_dir.exists():
            for path in sorted(self.processed_dir.glob("*_cleaned.csv")):
                try:
                    evidence.extend(self._summarise_file(path))
                except Exception as error:
                    print(f"Could not read {path.name}: {error}")

        return evidence

    # ---------- evidence from trusted documents ----------
    def retrieve_documents(self, question: str, limit: int = 2) -> list[dict]:
        """Keyword match over sections of files in docs/. Swap for Chroma/FAISS later."""
        if not self.docs_dir.exists():
            return []

        words = {w for w in re.findall(r"[a-z0-9]+", question.lower()) if len(w) > 3}
        scored = []
        for path in sorted(self.docs_dir.glob("*")):
            if path.suffix.lower() not in (".md", ".txt"):
                continue
            text = path.read_text(encoding="utf-8", errors="replace")
            sections = re.split(r"(?m)^#+\s+", text)
            for section in sections:
                if not section.strip():
                    continue
                heading, _, body = section.partition("\n")
                overlap = len(words & set(re.findall(r"[a-z0-9]+", section.lower())))
                if overlap:
                    scored.append((overlap, {
                        "source": str(path),
                        "row_id": f"section:{heading.strip()}",
                        "text": body.strip()[:400],
                    }))
        scored.sort(key=lambda pair: -pair[0])
        return [item for _, item in scored[:limit]]

    # ---------- checks ----------
    def check_evidence(self, question: str, evidence: list[dict]) -> dict:
        question_lower = question.lower()

        asks_about_pollution = any(
            re.search(rf"(?<![a-z0-9]){re.escape(term)}(?![a-z0-9])", question_lower)
            for term in POLLUTANT_TERMS
        )

        has_pollutant_data = False
        for item in evidence:
            data = item.get("data", {})
            if not isinstance(data, dict):
                continue
            for key in data:
                name = str(key).lower().strip()
                if name in POLLUTANT_EXACT or any(h in name for h in POLLUTANT_COLUMN_HINTS):
                    has_pollutant_data = True
                    break
            if has_pollutant_data:
                break

        supported = bool(evidence) and (not asks_about_pollution or has_pollutant_data)

        if supported:
            reason = "Evidence records were retrieved."
        elif not evidence:
            reason = "No evidence records were found in the cleaned data."
        else:
            reason = (
                "The available evidence does not support a reliable answer. "
                "Weather data alone does not establish pollutant levels."
            )

        return {
            "question": question,
            "supported": supported,
            "evidence_count": len(evidence),
            "reason": reason,
            "evidence": evidence,
        }

    # ---------- answer (numbers come from code, never from a model) ----------
    def generate_answer(
        self, question: str, evidence_check: dict, documents: list[dict] | None = None
    ) -> dict:
        documents = documents or []

        if not evidence_check["supported"]:
            return {
                "answer": "I don't know. " + evidence_check["reason"],
                "supported": False,
                "citations": [],
            }

        evidence = evidence_check["evidence"]
        aggregates = [
            e for e in evidence if str(e.get("row_id", "")).endswith(":aggregate")
        ]
        citations: list[dict] = []
        seen: set = set()

        def cite(source: str, row_id: str) -> None:
            if (source, row_id) not in seen:
                seen.add((source, row_id))
                citations.append({"source": source, "row_id": row_id})

        lines = []
        for item in aggregates:
            source = item["source"]
            file_name = Path(source).name
            cite(source, item["row_id"])
            for column, stats in item["data"].items():
                lines.append(
                    f"{column}: min {stats['min']:.2f} (row {stats['min_row']}), "
                    f"max {stats['max']:.2f} (row {stats['max_row']}), "
                    f"average {stats['mean']:.2f} over {stats['count']} values"
                )
                cite(source, f"{file_name}:{stats['min_row']}")
                cite(source, f"{file_name}:{stats['max_row']}")

        if lines:
            text = "Weather data summary: " + "; ".join(lines) + "."
        else:
            for item in evidence[:5]:
                cite(item.get("source", "unknown"), item.get("row_id", "unknown"))
            text = f"{len(evidence)} evidence records were retrieved; no numeric summary was possible."

        for doc in documents:
            cite(doc["source"], doc["row_id"])
            text += f" Guidance ({Path(doc['source']).name}, {doc['row_id']}): {doc['text']}"

        text += (
            " This is information, not professional advice; follow official "
            "services for emergencies. Interpret within the date range and coverage of the data."
        )
        return {"answer": text, "supported": True, "citations": citations}

    def validate_citations(self, answer: dict, evidence: list[dict]) -> bool:
        valid = {
            (item.get("source", "unknown"), item.get("row_id", "unknown"))
            for item in evidence
        }
        return all(
            (c.get("source", "unknown"), c.get("row_id", "unknown")) in valid
            for c in answer.get("citations", [])
        )

    # ---------- entry points ----------
    def ask(self, question: str) -> dict:
        evidence = self.retrieve_evidence(question)
        documents = self.retrieve_documents(question)
        check = self.check_evidence(question, evidence)
        answer = self.generate_answer(question, check, documents)
        return {
            "question": question,
            "answer": answer,
            "evidence_count": len(evidence),
            "citations_valid": self.validate_citations(answer, evidence + documents),
            "timestamp": datetime.now().isoformat(),
        }

    def run(self, question: str = "Summarize the available weather data."):
        print("\n=== AirGuard Insight Agent ===")
        report = self.ask(question)

        report_file = self.report_dir / "insight_report.json"
        with report_file.open("w", encoding="utf-8") as file:
            json.dump(report, file, indent=2, default=str)

        print(f"Answer: {report['answer']['answer']}")
        print(f"Evidence records: {report['evidence_count']}")
        print(f"Citations valid: {report['citations_valid']}")
        print(f"Insight report saved: {report_file}")
        return report


if __name__ == "__main__":
    InsightAgent().run()
