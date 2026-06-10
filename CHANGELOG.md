# Changelog

<!--next-version-placeholder-->

## NEXT

### New features

- **`get_historical_measurements()`** — fetch data for arbitrary date ranges, returns a wide-format `pandas.DataFrame`
  - Uses the async `POST /v2/report-requests` endpoint; polls until the report completes and downloads the result
  - Both `start_time` and `end_time` are fully respected; rate limit is 30 reports/org/day
- **`get_measurements_continuation()`** — stream new measurements without time-based race conditions
  - Uses `POST /v2/recent-datasource-measurements-continuation`; returns `(data, new_token)` tuples for chained polling

### Improvements

- **`get_recent_measurements()`** redesigned with explicit named parameters (breaking change from pre-1.0 `data=` dict style)
  - `datasource_ids` is now passed correctly as a list, fixing 400 errors on single-datasource queries
  - Pre-1.0 callers passing `data={...}` still work but emit a `DeprecationWarning`; the `data` parameter will be removed in a future version
- **Docstrings** updated for `get_recent_measurements()` (json-long return shape, lookback limits, `endTime` not supported) and `get_historical_measurements()` (wide-format return shape, rate limit now prominent)

### Internal

- `_get_report_status()` private helper added for debugging report request state

## v0.3.1 (2026-06-10)

- Fixed packaging: `pandas` is now correctly declared as a runtime dependency; `pytest` moved to optional `dev` dependency group.

## v0.3.0 (2024-08-26)

- `scale_raw_to_aqi()` function converts raw pollutant measurements to EPA AQI values.  Cutoff values come from https://www.airnow.gov/sites/default/files/2020-05/aqi-technical-assistance-document-sept2018.pdf,
    except for PM2.5 values which changed in 2024: https://www.epa.gov/system/files/documents/2024-02/pm-naaqs-air-quality-index-fact-sheet.pdf.

This package implemented the more strict values of PM2.5 in August 2024.  The EPA notes, "Many areas can expect to see more days in the Moderate (Code Yellow) category because of the changes in the AQI breakpoints. The Moderate category now begins when fine particle pollution concentrations reach 9 micrograms per cubic meter of air (the level of the updated annual air quality standard). Previously, the Moderate category began at 12 micrograms per cubic meter."

Thus users might see an apparent decrease in air quality with respect to PM2.5 occurring after updating to clarityio v0.3.0.

## v0.2.0 (2024-07-22)

- Can retrieve data in `csv-wide` format

## v0.1.0 (2024-07-07)

- Initial release