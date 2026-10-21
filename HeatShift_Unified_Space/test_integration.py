"""Check the adapters, citation evidence, and real dashboard interactions."""
import hashlib
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from integration import ROOT, CITIES, ask_insight, forecast_html, run_quality, training_evidence


class IntegrationTests(unittest.TestCase):
    def test_vendor_fingerprints(self):
        manifest = json.loads((ROOT / "evidence/integration_provenance.json").read_text())
        for name, sha in manifest["agents"].items():
            self.assertEqual(hashlib.sha256((ROOT / "vendor" / name).read_bytes()).hexdigest(), sha)

    def test_quality_decisions_and_unchanged_input(self):
        original = b"time,temperature_c\n2023-01-01T00:00,20\n2023-01-01T01:00,\n2023-01-01T02:00,24\n2023-01-01T02:00,24\n2023-01-01T03:00,100\n"
        report, cleaned = run_quality(original, "../../weather.csv")
        self.assertEqual(report["source"], "weather.csv")
        self.assertEqual(report["duplicates_removed"], 1)
        self.assertEqual(report["values_filled"], 1)
        self.assertEqual(report["weather_flags_total"], 1)
        self.assertIn(b"22.0", cleaned)
        self.assertEqual(report["input_sha256"], hashlib.sha256(original).hexdigest())

    def test_long_gaps_are_not_filled(self):
        report, _ = run_quality(b"time,temperature_c\n2023-01-01,20\n2023-01-02,\n2023-01-03,\n2023-01-04,\n2023-01-05,\n2023-01-06,24\n", "long.csv")
        self.assertEqual(report["values_filled"], 0)
        self.assertEqual(report["missing_values_after"], 4)

    def test_real_training_tables_and_zoned_time(self):
        total = 0
        for city in CITIES:
            frame = training_evidence(city)
            total += len(frame)
            report, _ = run_quality(frame.to_csv(index=False).encode(), "training.csv")
            self.assertEqual(report["rows_after"], len(frame))
            self.assertTrue(any("UTC" in note for note in report["integration_notes"]))
            self.assertIsNone(report["data_age_hours"])
        self.assertEqual(total, 16463)

    def test_insight_statistics_and_citations(self):
        for city in CITIES:
            frame = training_evidence(city)
            report = ask_insight(city, "Summarize recorded temperature.")
            self.assertTrue(report["citations_valid"])
            answer = report["answer"]["answer"]
            self.assertIn(f"average {frame.temperature_c.mean():.2f}", answer)
            self.assertIn(f"min {frame.temperature_c.min():.2f}", answer)
            self.assertIn(f"max {frame.temperature_c.max():.2f}", answer)
            for citation in report["answer"]["citations"]:
                row = citation["row_id"].rsplit(":", 1)[-1]
                self.assertTrue(row == "aggregate" or 0 <= int(row) < len(frame))

    def test_pollution_is_not_invented(self):
        report = ask_insight("Karachi", "What is the air quality or AQI?")
        self.assertFalse(report["answer"]["supported"])
        self.assertEqual(report["answer"]["citations"], [])

    def test_input_guards(self):
        with self.assertRaises(ValueError):
            training_evidence("unknown")
        with self.assertRaises(ValueError):
            run_quality(b"a\n1", "file.exe")
        with self.assertRaises(ValueError):
            run_quality(b"x" * (10 * 1024 * 1024 + 1), "large.csv")

    def test_forecast_bundle(self):
        html = forecast_html()
        self.assertNotIn('<script src=', html)
        self.assertNotIn('href="style.css"', html)
        self.assertIn('const bundledAssets=', html)
        self.assertIn('function bundledFetch(', html)
        self.assertIn('station_weather_model.json.gz', html)

    def test_streamlit_actions(self):
        from streamlit.testing.v1 import AppTest
        app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=30).run()
        self.assertEqual(len(app.exception), 0)
        self.assertEqual([tab.label for tab in app.tabs], ["🌡️ Prediction", "🔎 Data Quality", "💬 Insights", "ℹ️ Project status"])
        app.button[0].click().run()
        self.assertEqual(len(app.exception), 0)
        self.assertIn("quality_result", app.session_state)
        self.assertFalse(app.session_state["approved_cleaned"])
        app.checkbox[0].check().run()
        self.assertTrue(app.session_state["approved_cleaned"])
        app.selectbox[0].select("Lahore").run()
        self.assertFalse(app.session_state["approved_cleaned"])
        self.assertNotIn("quality_result", app.session_state)
        ask = next(button for button in app.button if button.label == "Ask insight agent")
        ask.click().run()
        self.assertEqual(len(app.exception), 0)
        self.assertTrue(app.session_state["insight_result"]["citations_valid"])
        app.selectbox[2].select("What is the air quality or AQI?").run()
        next(button for button in app.button if button.label == "Ask insight agent").click().run()
        self.assertFalse(app.session_state["insight_result"]["answer"]["supported"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
