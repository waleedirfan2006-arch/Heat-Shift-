
from pathlib import Path
import json

PROJECT_DIR = Path(__file__).resolve().parent
PROCESSED_DIR = PROJECT_DIR / "data" / "processed"
REPORT_DIR = PROJECT_DIR / "reports"

REPORT_DIR.mkdir(parents=True, exist_ok=True)


def load_json(path):
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def main():
    quality_data = load_json(PROCESSED_DIR / "quality_log.json")
    insight_data = load_json(REPORT_DIR / "insight_report.json")

    report_path = REPORT_DIR / "airguard_report.txt"

    with report_path.open("w", encoding="utf-8") as report:
        report.write("AIRGUARD DATA QUALITY REPORT\n")
        report.write("=" * 35 + "\n\n")

        report.write(f"Files processed: {len(quality_data)}\n\n")

        for item in quality_data:
            report.write(f"File: {item.get('source', item.get('source_file', 'Unknown'))}\n")
            report.write(f"Status: {item.get('status', 'processed')}\n")
            report.write(f"Rows before: {item.get('rows_before', item.get('original_rows', 'N/A'))}\n")
            report.write(f"Rows after: {item.get('rows_after', item.get('final_rows', 'N/A'))}\n")
            report.write(f"Duplicates removed: {item.get('duplicates_removed', 'N/A')}\n")
            report.write(f"Missing values remaining: {item.get('missing_values_after', 'N/A')}\n\n")

        report.write("\nINSIGHT SUMMARY\n")
        report.write("-" * 20 + "\n")

        for item in insight_data:
            report.write(f"\nFile: {item.get('file', 'Unknown')}\n")
            report.write(f"Rows analyzed: {item.get('rows', 'N/A')}\n")
            report.write(f"Columns: {', '.join(item.get('columns', []))}\n")
            report.write(f"Missing values: {item.get('missing_values', 'N/A')}\n")

    print(f"Report created: {report_path}")


if __name__ == "__main__":
    main()
