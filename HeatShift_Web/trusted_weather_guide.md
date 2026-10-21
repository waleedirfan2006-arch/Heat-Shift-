# Temperature prediction scope
HeatShift estimates the selected airport station's temperature at the same hour on the following day. Karachi, Lahore and Multan are supported. Historical training summaries describe recorded observations. They do not establish future conditions or pollutant levels. Source: the frozen model contract and station configuration in core.js.

# Uncertainty and baseline
The persistence baseline repeats the current measured station temperature. Mean absolute error measures average error in Celsius, and lower values are better. The displayed error range uses calibration residuals. Time dependence means future coverage is not guaranteed. This explanation does not establish whether an activity is safe. Source: the frozen evaluation metrics and model contract.

# Data quality and interpolation
The original Data Quality Agent removes exact duplicates, fills short interior numeric gaps, and flags implausible weather values. Filled data can use later rows. Review the decision log before using cleaned data for modeling and preserve time-based split boundaries. Source: preserved data_quality_agent.py, with its fingerprint in integration_provenance.json.

# Historical evidence and citations
Every numeric summary uses the selected city's canonical historical training table, identified by its SHA-256. Aggregate citations refer to that whole table. Extreme-value citations include the original NOAA source_row_id, row position, timestamp and temperature. Tables exclude targets and held-out splits. Source: gold_manifest.json and the cited table. Citation existence checks alone do not establish that a question falls within the supported scope; the adapter also checks the complete question.
