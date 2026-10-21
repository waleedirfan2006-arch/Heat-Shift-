# Integration verification

- 9 Python integration tests passed. They cover original-agent fingerprints, actual training data for all three cities, short and long gaps, duplicate and range decisions, citation/statistic checks, unsupported air-quality answers, input guards, bundled assets, and Streamlit button/approval/reset behavior.
- 12 DOM integration checks passed against the actual generated embedded forecast HTML. They exercise baseline, station-weather and JMA modes, errors, units, theme, tabs, city changes and session history. External weather responses were test fixtures, not measured live weather.
- 32 existing parser/input/weather-response checks passed after repairing the duplicate merge code.
- The agent sources match Mateen’s branch commit byte-for-byte. The original AirGuard path is untouched. The training-only evidence has 16,463 rows and excludes targets and held-out partitions.
- Test environment: Python 3.12; Streamlit 1.50.0; pandas 2.2.3; NumPy 2.3.5; Node.js with jsdom 26.1.0 for the embedded UI tests.
- Not verified: Hugging Face Docker build, production iframe rendering, mobile visual layout, live JMA availability and hourly scheduler integration. Previous Hugging Face sign-in was blocked by a 403 response. This package is not claimed as deployed.

Run Python checks from this folder with `python test_integration.py`. Run the existing source UI input checks from the repository root with `node HeatShift_Static_Space/test_browser_form.js`.
