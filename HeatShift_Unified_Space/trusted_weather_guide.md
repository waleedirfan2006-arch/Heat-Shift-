# Temperature prediction scope
HeatShift estimates the selected airport station's temperature exactly 24 hours after an observation. Karachi, Lahore and Multan are supported. Historical training summaries are not live weather and do not predict pollutant levels. Source: repository model contract and frozen model.

# Uncertainty and baseline
The declared baseline repeats the current measured station temperature. Lower mean absolute error in Celsius is better. Error ranges describe historical or calibration errors; time dependence means future coverage is not guaranteed. A forecast is not an official weather warning. Source: evidence/final_audit/primary_model/metrics.json.

# Data quality and interpolation
The unchanged Data Quality Agent removes exact duplicates, fills short interior numeric gaps of at most three rows, and flags implausible weather values. Filled data may use later rows and must be reviewed before any training use. Data age is unknown when the source clock has no reliable time zone. Source: preserved data_quality_agent.py and integration adapter.

# Historical evidence and citations
Insight statistics come from the selected city's training observations. Row numbers identify positions in the named cleaned table. Aggregate citations summarize the entire table. Citation validation checks that referenced records exist; it does not prove that every question has been fully answered. The original agent refuses AQI questions without pollutant evidence.
