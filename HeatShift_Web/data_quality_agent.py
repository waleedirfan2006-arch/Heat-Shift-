from pathlib import Path
from datetime import datetime
import json

import pandas as pd

# Gaps up to this many consecutive rows (hours) are filled and marked.
# Longer gaps are left missing and flagged (guide: do not guess).
MAX_FILL_GAP = 3
TIME_NAMES = ("time", "date", "datetime", "timestamp")
MAX_STORED_FLAGS = 500  # keep quality_log.json small; total is in the decision log


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


class DataQualityAgent:
    """Clean weather CSV files; decide fix / fill / flag and log every decision."""

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

    @staticmethod
    def _decide(decisions: list, file_name: str, column: str | None,
                rule: str, action: str, rows: int, reason: str) -> None:
        """Record one audited decision (action is fix, fill or flag)."""
        decisions.append({
            "timestamp": _now(),
            "file": file_name,
            "column": column,
            "rule": rule,
            "action": action,
            "rows_affected": int(rows),
            "reason": reason,
        })

    @staticmethod
    def _limits_for(name: str):
        if "humidity" in name or name in ("rh", "relative_humidity"):
            return (0, 100)
        if "temperature" in name or "dew_point" in name or name in ("temp", "t2m"):
            return (-90, 65)
        if "wind_speed" in name or name in ("windspeed", "wind speed"):
            return (0, 150)
        return None

    def process_file(self, file_path: Path) -> dict:
        file_path = Path(file_path)
        file_name = file_path.name
        decisions: list = []

        df = self._read_csv(file_path)
        original_rows = len(df)
        missing_before = int(df.isna().sum().sum())

        # 1. FIX: types. Convert likely numeric weather columns.
        numeric_tokens = (
            "temperature", "humidity", "dew_point", "pressure",
            "wind_speed", "wind_direction", "precipitation",
            "rain", "snow", "cloud", "visibility", "radiation",
        )
        for column in df.columns:
            name = column.lower().strip()
            is_time = name in TIME_NAMES
            looks_numeric = any(t in name for t in numeric_tokens) or name in (
                "temp", "t2m", "rh", "windspeed"
            )
            if looks_numeric and not is_time and not pd.api.types.is_numeric_dtype(df[column]):
                before = int(df[column].notna().sum())
                df[column] = pd.to_numeric(df[column], errors="coerce")
                coerced = before - int(df[column].notna().sum())
                self._decide(
                    decisions, file_name, column, "numeric_type_check", "fix",
                    before,
                    f"Column was text; converted to number. {coerced} values "
                    "could not be read and became missing (kept visible).",
                )

        # 2. FIX: time column to datetime. Time zone is not stated in the file.
        time_col = next(
            (c for c in df.columns if c.lower().strip() in TIME_NAMES), None
        )
        if time_col is not None:
            parsed = pd.to_datetime(df[time_col], errors="coerce")
            bad_times = int(parsed.isna().sum())
            df[time_col] = parsed
            self._decide(
                decisions, file_name, time_col, "time_zone_check", "flag",
                len(df),
                "File does not state a time zone. Treated as UTC; convert to "
                "PKT only for display and verify before merging sources.",
            )
            if bad_times:
                self._decide(
                    decisions, file_name, time_col, "time_parse_check", "flag",
                    bad_times, "Timestamps that could not be parsed were kept as missing.",
                )

        # 3. FIX: remove exact duplicate rows (safe and certain).
        df = df.drop_duplicates().copy()
        rows_after_dedup = len(df)
        removed = original_rows - rows_after_dedup
        if removed:
            self._decide(
                decisions, file_name, None, "exact_duplicate_rows", "fix",
                removed, "Exact duplicate rows removed; first copy kept.",
            )

        if time_col is not None:
            df = df.sort_values(time_col).reset_index(drop=True)
        else:
            df = df.reset_index(drop=True)

        # 4. FLAG: impossible values (left unchanged, never silently edited).
        weather_flags = []
        flagged_total = 0
        for column in df.select_dtypes(include="number").columns:
            limits = self._limits_for(column.lower().strip())
            if limits is None:
                continue
            invalid = df[column].notna() & (
                (df[column] < limits[0]) | (df[column] > limits[1])
            )
            count = int(invalid.sum())
            if not count:
                continue
            flagged_total += count
            self._decide(
                decisions, file_name, column, "range_check", "flag", count,
                f"Values outside expected range {list(limits)}; cannot be "
                "confirmed as errors, so they are kept and flagged.",
            )
            for index in df.index[invalid]:
                if len(weather_flags) < MAX_STORED_FLAGS:
                    weather_flags.append({
                        "row": int(index),
                        "column": column,
                        "value": float(df.at[index, column]),
                        "issue": "outside_expected_range",
                        "expected_range": list(limits),
                    })

        missing_before_fill = int(df.isna().sum().sum())

        # 5. FILL short gaps (marked) / FLAG long gaps (left missing).
        values_filled = 0
        for column in list(df.select_dtypes(include="number").columns):
            mask = df[column].isna()
            n_missing = int(mask.sum())
            if not n_missing:
                continue

            run_id = (mask != mask.shift()).cumsum()
            run_len = mask.groupby(run_id).transform("sum")
            short = mask & (run_len <= MAX_FILL_GAP)

            interpolated = df[column].interpolate(
                method="linear", limit_area="inside"
            )
            fillable = short & interpolated.notna()
            df.loc[fillable, column] = interpolated[fillable]
            df[f"{column}_filled"] = fillable  # keeps every filled value visible

            n_fill = int(fillable.sum())
            n_flag = n_missing - n_fill
            values_filled += n_fill

            if n_fill:
                self._decide(
                    decisions, file_name, column, f"short_gap_le_{MAX_FILL_GAP}",
                    "fill", n_fill,
                    f"Gaps of {MAX_FILL_GAP} rows or fewer were linearly "
                    f"interpolated and marked in '{column}_filled'.",
                )
            if n_flag:
                self._decide(
                    decisions, file_name, column, f"long_gap_gt_{MAX_FILL_GAP}",
                    "flag", n_flag,
                    "Long gap or gap at the edge of the series; not guessed, "
                    "left as missing.",
                )

        data_cols = [c for c in df.columns if not c.endswith("_filled")]
        missing_after = int(df[data_cols].isna().sum().sum())
        missing_numeric_after = int(
            df[data_cols].select_dtypes(include="number").isna().sum().sum()
        )

        latest_time = None
        age_hours = None
        if time_col is not None and df[time_col].notna().any():
            latest = df[time_col].max()
            latest_time = latest.isoformat()
            age_hours = round((datetime.now() - latest.to_pydatetime()).total_seconds() / 3600, 1)

        source_group = file_path.parent.name
        output_file = self.output_dir / f"{source_group}_{file_path.stem}_cleaned.csv"
        df.to_csv(output_file, index=False)

        return {
            "source": str(file_path),
            "output": str(output_file),
            "source_type": source_group,
            "rows_before": original_rows,
            "rows_after": len(df),
            "duplicates_removed": removed,
            "missing_values_before": missing_before,
            "missing_values_before_fill": missing_before_fill,
            "missing_values_after": missing_after,
            "missing_numeric_values_after_fill": missing_numeric_after,
            "remaining_missing_values_flagged": missing_after,
            "values_filled": values_filled,
            "weather_flags": weather_flags,
            "weather_flags_total": flagged_total,
            "latest_data_time": latest_time,
            "data_age_hours": age_hours,
            "decisions": decisions,
            "status": "processed",
            "timestamp": _now(),
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
                    f"({report['rows_before']} rows -> {report['rows_after']} rows, "
                    f"{len(report['decisions'])} decisions)"
                )
            except Exception as error:
                reports.append({
                    "source": str(file_path),
                    "status": "error",
                    "error": str(error),
                    "timestamp": _now(),
                })
                print(f"Could not process {file_path.name}: {error}")

        log_file = self.output_dir / "quality_log.json"
        with log_file.open("w", encoding="utf-8") as file:
            json.dump(reports, file, indent=2, default=str)

        succeeded = sum(item.get("status") == "processed" for item in reports)
        failed = len(reports) - succeeded

        print(f"\nFinished. {succeeded} processed; {failed} failed.")
        print(f"Quality log: {log_file}")

        return reports


if __name__ == "__main__":
    DataQualityAgent().run()
