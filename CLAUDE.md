# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Setup

`.venv` is inside the repo and gitignored. To recreate: `python3 -m venv .venv && .venv/bin/pip install -e ".[dev]"` then `source .venv/bin/activate`.

## Architecture

**clarityio** is a Python library wrapping the [Clarity.io](https://clarity.io) API v2 for retrieving air quality sensor data. The API docs are https://api-guide.clarity.io/index.html.

- **`src/clarityio/clarityio.py`** — `ClarityAPIConnection` class. Authenticated via API key + mandatory `org` parameter on every call. Three methods map to API endpoints: `get_recent_measurements()` (POST), `get_datasources()` (GET), `get_datasource_details()` (GET). All methods catch exceptions and return `None` on failure rather than raising.

- **`src/clarityio/scaling.py`** — `scale_raw_to_aqi()` function. Converts raw pollutant measurements to EPA AQI (0–500 scale) using linear interpolation between EPA breakpoints. Accepts a single float or a pandas Series. Handles PM10, PM2.5, CO, SO₂, NO₂, O₃ (1hr and 8hr). PM2.5 breakpoints were updated in 2024.
