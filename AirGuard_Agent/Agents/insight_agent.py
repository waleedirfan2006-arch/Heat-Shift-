
from pathlib import Path
from typing import Any
from datetime import datetime
import json

import pandas as pd


class InsightAgent:
    """Evidence-first insight helper for AirGuard."""

    def __init__(self, retriever: Any = None, data_store: Any = None):
        self.retriever = retriever
        self.data_store = data_store

        self.project_dir = Path(__file__).resolve().parent.parent
        self.processed_dir = self.project_dir / "data" / "processed"
        self.report_dir = self.processed_dir
        self.report_dir.mkdir(parents=True, exist_ok=True)

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

        # Read sample records from cleaned CSV files if needed.
        if not evidence and self.processed_dir.exists():
            for path in sorted(
                self.processed_dir.glob("*_cleaned.csv")
            ):
                try:
                    frame = pd.read_csv(path)
                except Exception as error:
                    print(f"Could not read {path.name}: {error}")
                    continue

                for row_number, row in frame.iterrows():
                    evidence.append({
                        "source": str(path),
                        "row_id": f"{path.name}:{row_number}",
                        "data": row.where(
                            pd.notna(row), None
                        ).to_dict(),
                    })

        return evidence

    def check_evidence(
        self, question: str, evidence: list[dict]
    ) -> dict:
        question_lower = question.lower()

        pollutant_terms = (
            "pollution", "pollutant", "pm2.5", "pm25",
            "pm10", "aqi", "air quality", "ozone",
            "no2", "so2", "co",
        )

        asks_about_pollution = any(
            term in question_lower for term in pollutant_terms
        )

        pollutant_columns = {
            "pm2.5", "pm25", "pm10", "aqi",
            "ozone", "no2", "so2", "co",
        }

        has_pollutant_data = False

        for item in evidence:
            data = item.get("data", {})

            if not isinstance(data, dict):
                continue

            column_names = {
                str(key).lower().strip() for key in data
            }

            if any(
                name in pollutant_columns
                or "pm2.5" in name
                or "pm25" in name
                or "pm10" in name
                or "ozone" in name
                for name in column_names
            ):
                has_pollutant_data = True
                break

        supported = bool(evidence) and (
            not asks_about_pollution or has_pollutant_data
        )

        if supported:
            reason = "Evidence records were retrieved."
        else:
            reason = (
                "The available evidence does not support a reliable "
                "answer. Weather data alone does not establish "
                "pollutant levels."
            )

        return {
            "question": question,
            "supported": supported,
            "evidence_count": len(evidence),
            "reason": reason,
            "evidence": evidence,
        }

    

    def validate_citations(
        self, answer: dict, evidence: list[dict]
    ) -> bool:
        valid_citations = {
            (
                item.get("source", "unknown"),
                item.get("row_id", "unknown"),
            )
            for item in evidence
        }

        return all(
            (
                citation.get("source", "unknown"),
                citation.get("row_id", "unknown"),
            ) in valid_citations
            for citation in answer.get("citations", [])
        )

    def run(self):
        print("\n=== AirGuard Insight Agent ===")

        question = "Summarize the available weather data."

        evidence = self.retrieve_evidence(question)
        evidence_check = self.check_evidence(question, evidence)
        answer = self.generate_answer(question, evidence_check)

        citations_valid = self.validate_citations(
            answer, evidence
        )

        report = {
            "question": question,
            "answer": answer,
            "evidence_count": len(evidence),
            "citations_valid": citations_valid,
            "timestamp": datetime.now().isoformat(),
        }

        report_file = self.report_dir / "insight_report.json"

        with report_file.open("w", encoding="utf-8") as file:
            json.dump(report, file, indent=2, default=str)

        print(f"Answer: {answer['answer']}")
        print(f"Evidence records: {len(evidence)}")
        print(f"Citations valid: {citations_valid}")
        print(f"Insight report saved: {report_file}")

        return report


if __name__ == "__main__":
    InsightAgent().run()
