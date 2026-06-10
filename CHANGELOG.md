# Changelog

<!--next-version-placeholder-->

## v1.0.0 (2026-06-10)

- `get_historical_measurements()` — new method for arbitrary date ranges via the async `POST /v2/report-requests` endpoint. Accepts `start_time` and `end_time`, polls until the report completes, downloads the result, and returns a `pandas.DataFrame`. Both time bounds are fully respected. Rate limit is 30 reports/org/day.
- `get_measurements_continuation()` — new method for streaming new measurements without time-based race conditions, using the `POST /v2/recent-datasource-measurements-continuation` endpoint. Returns `(data, new_token)` tuples for chained polling.
- `get_recent_measurements()` redesigned with explicit named parameters replacing the open `data` dict. `datasource_ids` is now passed correctly as a list (`datasourceIds: [...]`), fixing 400 errors on single-datasource queries. The docstring documents the 48-hour (hourly) and 10-day (daily) lookback limits and that `endTime` is not supported by this endpoint.
- `_get_report_status()` private helper added for debugging report request state.
- Version bump to 1.0.0.

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