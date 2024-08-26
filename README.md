# clarityio

This package wraps the API for Clarity air quality sensors.  It makes calls to [v2 of the API](https://api-guide.clarity.io/), which as of August 2024 is the newest version of the API.


## Development status

This package is in beta status.  Some functionality is still missing, but it is being used in production at the City of Ann Arbor. 

### Implemented endpoints

- Recent measurements: `POST {baseUrl}/v2/recent-datasource-measurements-query `
- Per-Org Datasources summary: `GET {baseURl}/v2/datasources`
- Per-Datasource details: `GET {baseURl}/v2/datasources/:datasourceId `

### Not yet implemented

- Continuations
- Historical measurements
- All other endpoints.


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

See API docs for valid arguments to pass, e.g., retrieve daily data instead of hourly.  

The default value of `format` is `json-long`, which returns the data in long format (one row per combination of metric and time).  Here is such a call:

```python
request_body = {
        'allDatasources': True,
        'outputFrequency': 'hour',
        'format': 'json-long',
        'startTime': '2024-07-22T00:00:00Z'
}
response = api_connection.get_recent_measurements(data=request_body)
df = pd.DataFrame(response['data'])
```

To get the data in wide format, with one row per timestamp and each metric in its own column, use the `csv-wide` format option and convert to a pandas dataframe:

```python
request_body = {
        'allDatasources': True,
        'outputFrequency': 'hour',
        'format': 'csv-wide',
        'metricSelect': 'only pm2_5ConcMass24HourRollingMean' # Refer to API documentation for metric selection
}
response_wide = api_connection.get_recent_measurements(data=request_body)
from io import StringIO
df_wide = pd.read_csv(StringIO(response_wide), sep=",")
```

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