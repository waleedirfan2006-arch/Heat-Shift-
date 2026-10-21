# Choose a CSV for your dashboard demonstration

**Real data:** `Karachi_Weather_Training_5012.csv` contains 5,012 repository NOAA training rows. They are already clean, so the agent should show zero fills and range flags. It may still flag the missing timezone label.

**Practice the fix/fill/flag feature:** `HeatShift_QA_Practice_SAMPLE_SYNTHETIC.csv` is deliberately fabricated for demonstration, not real weather or a live reading. It has one repeated row, two short missing gaps, four consecutive missing values, and one value of 80 C. The agent should remove the duplicate, fill and mark the short gaps, and leave long gaps and the out-of-range value visible with flags.

In the dashboard, click **Data quality** in the left menu → **Choose a CSV file** → select one of these files → **Run quality agent on CSV**. First use may take about a minute while Python loads. Read the decision list. Filled values have a `*_filled` marker. Tick the review box only after reading the report, then download the cleaned CSV or JSON log.

For a traceable insight, click **Insights** → **Temperature summary** → **Ask agent**. Read the source row IDs below the answer. Click **Check evidence limits**, then **Ask agent**, to see an unsupported AQI question refused.

For prediction, choose a city, click **Prediction**, then **Use latest airport observation** and **Run 24-hour prediction**. Manual reports must be real on-the-hour readings from the last four hours. Prediction does not use the old CSV as current weather.
