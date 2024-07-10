import requests

class ClarityAPIConnection:
    def __init__(self, api_key, org):
        self.base_url = "https://clarity-data-api.clarity.io/v2/"
        self.api_key = api_key
        self.org = org
        self.headers = {
            "Accept-Encoding": "gzip, deflate, br",
            "x-api-key": self.api_key
        }
    
    def get_recent_measurements(self, data=None):
        endpoint = 'recent-datasource-measurements-query'
        url = f"{self.base_url}{endpoint}"
        if data is None:
            print('No parameters provided, fetching hourly measurements for all datasources using API defaults.')
            data = {}
            data['allDatasources'] = True
            data['outputFrequency'] = 'hour' # API v2 docs say this should be a default value but requests fails w/o it
        data['org'] = self.org
        try:
            response = requests.post(url, headers=self.headers, json=data)
            response.raise_for_status()  # Raises an HTTPError if the response status code is 4XX/5XX
            return response.json()
        except requests.exceptions.HTTPError as err:
            print(f"HTTP error occurred: {err}")
        except Exception as err:
            print(f"An error occurred: {err}")
    
    def get_datasources(self):
        """
        Fetches datasources for the organization using a GET request.
        Returns:
            dict: The JSON response from the API.
        """
        endpoint = 'datasources'
        url = f"{self.base_url}{endpoint}"
        params = {'org': self.org}  # Using org from the instance variable
        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as err:
            print(f"HTTP error occurred: {err}")
        except Exception as err:
            print(f"An error occurred: {err}")
    
    def get_datasource_details(self, datasourceId):
        """
        Fetches details for a specific datasource using its ID and includes the organization in the query parameters.
        Args:
            datasourceId (str): The ID of the datasource to fetch details for.
        Returns:
            dict: The JSON response from the API.
        """
        endpoint = f'datasources/{datasourceId}'  # Insert the datasourceId into the URL
        url = f"{self.base_url}{endpoint}"
        params = {'org': self.org}  # Include the organization in the query parameters
        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()  # Raises an HTTPError if the response status code is 4XX/5XX
            return response.json()
        except requests.exceptions.HTTPError as err:
            print(f"HTTP error occurred: {err}")
        except Exception as err:
            print(f"An error occurred: {err}")