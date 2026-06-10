# clarityio

This package wraps the API for Clarity air quality sensors.  It makes calls to [v2 of the API](https://api-guide.clarity.io/), which as of June 2026 is the newest version of the API.


## Development status

This package is stable and used in production at the City of Ann Arbor.

### Implemented endpoints

- Recent measurements: `POST {baseUrl}/v2/recent-datasource-measurements-query`
- Recent measurements continuation: `POST {baseUrl}/v2/recent-datasource-measurements-continuation`
- Historical measurements: `POST {baseUrl}/v2/report-requests`
- Per-Org Datasources summary: `GET {baseUrl}/v2/datasources`
- Per-Datasource details: `GET {baseUrl}/v2/datasources/:datasourceId`

### Not yet implemented

- Devices / nodes: `GET {baseUrl}/v2/devices/nodes` and per-node detail/status
- Subscriptions: `GET {baseUrl}/v2/subscriptions`
- Metrics dictionary and other reference endpoints


## Installation

Install from PyPI:
```
pip install clarityio
```

## Usage

### Initialize API connection

Find your API key and org in your Clarity.io user profile.  Log in at https://dashboard.clarity.io, then click the person icon on the top-right corner.

Use these values to initialize a connection:

```python
import clarityio
import pandas as pd
api_connection = clarityio.ClarityAPIConnection(api_key='YOUR_API_KEY', org='YOUR_ORG')
```
Both of these values are required to make calls to the Clarity API and are appended as needed by this package.

### Retrieve recent measurements

The API limits how far back this endpoint can look (e.g., 48 hours for hourly data). For older data or bounded time windows, use `get_historical_measurements()` instead.

The default `format` is `json-long`, which returns one row per combination of metric and time:

```python
response = api_connection.get_recent_measurements(
    all_datasources=True,
    output_frequency='hour',
    start_time='2024-07-22T00:00:00Z',
)
df = pd.DataFrame(response['data'])
```

To get wide format (one row per timestamp, each metric in its own column):

```python
from io import StringIO
response_wide = api_connection.get_recent_measurements(
    all_datasources=True,
    output_frequency='hour',
    format='csv-wide',
    metric_select='only pm2_5ConcMass24HourRollingMean',  # see API docs for metric selection
)
df_wide = pd.read_csv(StringIO(response_wide))
```

### Stream new measurements with a continuation token

To poll for new data without time-based race conditions, seed a continuation
token and pass it back on each subsequent call. Each call returns only data that
arrived since the previous one. Tokens are valid for 24 hours.

```python
import time

# Seed a token from an initial recent-measurements call
data, token = api_connection.get_recent_measurements(
    datasource_ids=['A_DATA_SOURCE_ID'],
    reply_with_continuation_token=True,
)

# On each poll, pass the latest token to get only new data
while True:
    time.sleep(60)
    data, token = api_connection.get_measurements_continuation(token)
    if data:
        ...  # process new measurements
```

### Retrieve historical measurements

Use this for arbitrary date ranges or data older than the recent-measurements lookback limits. The method submits an async report, polls until ready, and returns a wide-format DataFrame. Note that the API allows **30 reports per org per day**.

```python
df = api_connection.get_historical_measurements(
    start_time='2024-01-01T00:00:00Z',
    end_time='2024-01-31T00:00:00Z',
    all_datasources=True,
    output_frequency='hour',
)
```

The returned DataFrame has one row per datasource/time-period. The timestamp column is `startOfPeriod` and metric columns follow the pattern `{metricName}.value` (e.g. `pm2_5ConcMass1HourMean.value`).

### List data sources
```python
datasources_response = api_connection.get_datasources()
datasources = pd.json_normalize(datasources_response['datasources'])
```

### Get details for a specific data source

Obtain the IDs from the prior block of code.
```python
source_details_response = api_connection.get_datasource_details('A_DATA_SOURCE_ID')
source_details = pd.json_normalize(source_details_response['datasource'])
```

### Convert a raw measurement to the EPA AQI scale

The Clarity API provides some of these values, but this utility function offers more flexibility for custom data processing.
```python
clarityio.scale_raw_to_aqi('pm2.5_24hr', 18.84) # 69.14676806083651
clarityio.scale_raw_to_aqi('nitrogen_dioxide_1hr', 300) # 138.64864864864865
```