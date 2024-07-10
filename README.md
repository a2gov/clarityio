# clarityio

This package wraps the API for Clarity air quality sensors.  It makes calls to [v2 of the API](https://api-guide.clarity.io/), which as of July 2024 is the newest version of the API.


## Development status

This package is in alpha status, currently being developed and subject to major changes. 

### Implemented endpoints

- Recent measurements: `POST {baseUrl}/v2/recent-datasource-measurements-query `
- Per-Org Datasources summary: `GET {baseURl}/v2/datasources`
- Per-Datasource details: `GET {baseURl}/v2/datasources/:datasourceId `

### Not yet implemented

- Continuations
- Historical measurements
- All other endpoints.


## Usage

### Initialize API connection

Find your API key and org in your Clarity.io user profile.  Log in at https://dashboard.clarity.io, then click the person icon on the top-right corner.

Use these values to initialize a connection:

```python
import clarityio
import pandas as pd
api_connection = clarityio.ClarityAPIConnection(api_key='YOUR_API_KEY', org='YOUR_ORG')
```

### Retrieve recent measurements

See API docs for valid arguments to pass, e.g., retrieve daily data instead of hourly, or in CSV format instead of JSON.

```python
request_body = { # the required value for 'org' is automatically passed from the connection object
        'allDatasources': True,
        'outputFrequency': 'hour',
        'format': 'json-long',
        'startTime': '2024-07-05T00:00:00Z'
}
response = api_connection.get_recent_measurements(data=request_body)
df = pd.DataFrame(response['data'])
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