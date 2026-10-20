
from pathlib import Path
from datetime import datetime
import json

import pandas as pd


class DataQualityAgent:
    """Clean weather CSV files and record data quality results."""

    def __init__(self):
        self.project_dir = Path(__file__).resolve().parent.parent
        self.input_dir = self.project_dir / "agents" / "data" / "raw"
        self.output_dir = self.project_dir / "data" / "processed"
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _read_csv(self, file_path: Path) -> pd.DataFrame:
        """Read NOAA and Open-Meteo CSV files."""
        is_open_meteo = (
            "open-meteo" in file_path.name.lower()
            or "open_meteo" in str(file_path.parent).lower()
        )

        if is_open_meteo:
            df = pd.read_csv(file_path, skiprows=3)
        else:
            df = pd.read_csv(file_path)

        df.columns = [str(col).strip() for col in df.columns]
        df = df.dropna(axis=1, how="all")
        return df

    def process_file(self, file_path: Path) -> dict:
        file_path = Path(file_path)
        df = self._read_csv(file_path)

        original_rows = len(df)
        missing_before = int(df.isna().sum().sum())
        duplicate_count = int(df.duplicated().sum())

        weather_flags = []

        # Convert likely numeric weather columns.
        numeric_tokens = (
            "temperature", "humidity", "dew_point", "pressure",
            "wind_speed", "wind_direction", "precipitation",
            "rain", "snow", "cloud", "visibility", "radiation",
        )

        for column in df.columns:
            name = column.lower().strip()
            if any(token in name for token in numeric_tokens) or name in (
                "temp", "t2m", "rh", "windspeed"
            ):
                df[column] = pd.to_numeric(df[column], errors="coerce")

        # Flag suspicious values; do not silently change them.
        for column in df.select_dtypes(include="number").columns:
            name = column.lower().strip()
            limits = None

            if "humidity" in name or name in ("rh", "relative_humidity"):
                limits = (0, 100)
            elif (
                "temperature" in name
                or "dew_point" in name
                or name in ("temp", "t2m")
            ):
                limits = (-90, 65)
            elif "wind_speed" in name or name in ("windspeed", "wind speed"):
                limits = (0, 150)
            elif "relative_humidity" in name:
                limits = (0, 100)

            if limits is not None:
                invalid = df[column].notna() & (
                    (df[column] < limits[0])
                    | (df[column] > limits[1])
                )

                for index in df.index[invalid]:
                    weather_flags.append({
                        "row": int(index),
                        "column": column,
                        "value": float(df.at[index, column]),
                        "issue": "outside_expected_range",
                        "expected_range": list(limits),
                    })

        # Remove exact duplicate rows.
        df = df.drop_duplicates().copy()
        rows_after_deduplication = len(df)

        # Record missing values after conversion and deduplication,
        # before filling any values.
        missing_before_fill = int(df.isna().sum().sum())

        # Fill missing numeric values with the median where available.
        for column in df.select_dtypes(include="number").columns:
            if df[column].isna().any():
                median = df[column].median()
                if pd.notna(median):
                    df[column] = df[column].fillna(median)

        missing_after = int(df.isna().sum().sum())
        missing_numeric_after_fill = int(
            df.select_dtypes(include="number").isna().sum().sum()
        )

        # Keep output filenames unique across source folders.
        source_group = file_path.parent.name
        output_file = (
            self.output_dir
            / f"{source_group}_{file_path.stem}_cleaned.csv"
        )
        df.to_csv(output_file, index=False)

        return {
            "source": str(file_path),
            "output": str(output_file),
            "source_type": source_group,
            "rows_before": original_rows,
            "rows_after": len(df),
            "duplicates_removed": original_rows - rows_after_deduplication,
            "missing_values_before": missing_before,
            "missing_values_before_fill": missing_before_fill,
            "missing_values_after": missing_after,
            "missing_numeric_values_after_fill": missing_numeric_after_fill,
            "remaining_missing_values_flagged": missing_after,
            "weather_flags": weather_flags,
            "status": "processed",
            "timestamp": datetime.now().isoformat(timespec="seconds"),
        }

    def run(self):
        reports = []

        if not self.input_dir.exists():
            raise FileNotFoundError(
                f"Raw data folder was not found: {self.input_dir}"
            )

        files = sorted(self.input_dir.rglob("*.csv"))

        if not files:
            print(f"No CSV files found in {self.input_dir}")

        for file_path in files:
            try:
                report = self.process_file(file_path)
                reports.append(report)

                print(
                    f"Processed: {file_path.name} "
                    f"({report['rows_before']} rows -> "
                    f"{report['rows_after']} rows)"
                )
            except Exception as error:
                reports.append({
                    "source": str(file_path),
                    "status": "error",
                    "error": str(error),
                    "timestamp": datetime.now().isoformat(timespec="seconds"),
                })
                print(f"Could not process {file_path.name}: {error}")

        log_file = self.output_dir / "quality_log.json"
        with log_file.open("w", encoding="utf-8") as file:
            json.dump(reports, file, indent=2)

        succeeded = sum(
            item.get("status") == "processed" for item in reports
        )
        failed = len(reports) - succeeded

        print(f"\nFinished. {succeeded} processed; {failed} failed.")
        print(f"Quality log: {log_file}")

        return reports


if __name__ == "__main__":
    DataQualityAgent().run()
