import copy
import io
import time
import warnings

import pandas as pd
import requests


class ClarityAPIConnection:
    def __init__(self, api_key, org):
        self.base_url = "https://clarity-data-api.clarity.io/v2/"
        self.api_key = api_key
        self.org = org
        self.headers = {
            "Accept-Encoding": "gzip, deflate, br",
            "x-api-key": self.api_key,
        }

    def _resolve_datasource_params(self, datasource_ids, all_datasources):
        if datasource_ids is not None and all_datasources:
            raise ValueError("Specify either datasource_ids or all_datasources=True, not both.")
        if datasource_ids is not None:
            return {"datasourceIds": list(datasource_ids)}
        return {"allDatasources": True}

    def _format_time(self, t):
        if t is None:
            return None
        if hasattr(t, "isoformat"):
            return t.isoformat()
        return t

    def get_recent_measurements(
        self,
        datasource_ids=None,
        all_datasources=None,
        output_frequency="hour",
        start_time=None,
        metric_select=None,
        format="json-long",
        qc_assessment=False,
        qc_flags=False,
        reply_with_continuation_token=False,
        data=None,
    ):
        """Retrieve recent measurements from the Clarity.io API.

        Wraps POST /v2/recent-datasource-measurements-query.

        Time window limits enforced by the API:
          - minute frequency: 24-hour lookback max
          - hour frequency:   48-hour lookback max
          - day frequency:    10-day lookback max

        endTime is NOT supported by this endpoint. For bounded time windows or
        data older than the limits above, use get_historical_measurements().

        NOTE on return shapes: this method and get_historical_measurements() return
        data in different shapes. This method's json-long format is a dict with a
        'data' key containing records like {datasourceId, time, metric, value, raw}.
        get_historical_measurements() returns a wide-format DataFrame where the time
        column is 'startOfPeriod' and metric columns are named '{metric}.value'.
        There is currently no shared transform pipeline between the two.

        Args:
            datasource_ids: List of datasource ID strings. Mutually exclusive with
                all_datasources. Defaults to all datasources if omitted.
            all_datasources: If True, query all org datasources.
            output_frequency: 'minute', 'hour' (default), or 'day'.
            start_time: ISO 8601 string or datetime. Subject to lookback limits.
            metric_select: Optional metric filter string.
            format: 'json-long' (default) or 'csv-wide'.
            qc_assessment: Include QC assessment field in metrics.
            qc_flags: Include QC flags field in metrics.
            reply_with_continuation_token: If True, returns (data, token) tuple
                for use with get_measurements_continuation().
            data: Deprecated. Pass a raw request-body dict directly, matching
                the pre-1.0 interface. Use explicit keyword arguments instead.

        Returns:
            json-long: dict with 'data' key — list of {datasourceId, time (UTC ISO
                8601), metric (canonical name), value (calibrated), raw} records.
            csv-wide: raw CSV string.
            None on error.
            If reply_with_continuation_token=True, returns (data, token_str | None).
        """
        if data is not None:
            warnings.warn(
                "The 'data' parameter is deprecated and will be removed in a future version. "
                "Pass individual keyword arguments instead (datasource_ids, start_time, etc.).",
                DeprecationWarning,
                stacklevel=2,
            )
            url = f"{self.base_url}recent-datasource-measurements-query"
            payload = copy.deepcopy(data)
            payload["org"] = self.org
            try:
                response = requests.post(url, headers=self.headers, json=payload)
                response.raise_for_status()
            except requests.exceptions.HTTPError as err:
                print(f"HTTP error occurred: {err}")
                return None
            except Exception as err:
                print(f"An error occurred: {err}")
                return None
            return response.text if payload.get("format") == "csv-wide" else response.json()

        url = f"{self.base_url}recent-datasource-measurements-query"
        body = {"org": self.org, "outputFrequency": output_frequency, "format": format}
        body.update(self._resolve_datasource_params(datasource_ids, all_datasources))
        if start_time is not None:
            body["startTime"] = self._format_time(start_time)
        if metric_select is not None:
            body["metricSelect"] = metric_select
        if qc_assessment:
            body["qcAssessment"] = True
        if qc_flags:
            body["qcFlags"] = True
        if reply_with_continuation_token:
            body["replyWithContinuationToken"] = True

        try:
            response = requests.post(url, headers=self.headers, json=body)
            response.raise_for_status()
        except requests.exceptions.HTTPError as err:
            print(f"HTTP error occurred: {err}")
            return (None, None) if reply_with_continuation_token else None
        except Exception as err:
            print(f"An error occurred: {err}")
            return (None, None) if reply_with_continuation_token else None

        token = response.headers.get("x-clarity-continuation-token")
        result = response.text if format == "csv-wide" else response.json()
        if reply_with_continuation_token:
            return (result, token)
        return result

    def get_measurements_continuation(self, continuation_token):
        """Poll for new measurements using a continuation token.

        Wraps POST /v2/recent-datasource-measurements-continuation. Use this to
        stream new measurements without time-based race conditions.

        Args:
            continuation_token: Token from a prior get_recent_measurements() call
                (with reply_with_continuation_token=True) or a prior call here.
                Tokens are valid for 24 hours.

        Returns:
            Tuple of (data, new_continuation_token), or (None, None) on error.
        """
        url = f"{self.base_url}recent-datasource-measurements-continuation"
        body = {"org": self.org, "continuationToken": continuation_token}
        try:
            response = requests.post(url, headers=self.headers, json=body)
            response.raise_for_status()
        except requests.exceptions.HTTPError as err:
            print(f"HTTP error occurred: {err}")
            return None, None
        except Exception as err:
            print(f"An error occurred: {err}")
            return None, None

        new_token = response.headers.get("x-clarity-continuation-token")
        return response.json(), new_token

    def get_historical_measurements(
        self,
        start_time,
        end_time,
        datasource_ids=None,
        all_datasources=None,
        output_frequency="hour",
        metric_select=None,
        file_format="csv",
        metric_label_style="canonical",
        poll_interval=15,
        timeout=600,
    ):
        """Retrieve historical measurements for an arbitrary date range.

        Wraps the asynchronous POST /v2/report-requests endpoint. Submits a
        report, polls until completion, downloads result file(s), and returns a
        single concatenated DataFrame. Both startTime and endTime are fully
        respected; there is no lookback cap.

        RATE LIMIT: 30 reports per organization per day, resetting at UTC
        midnight. This limit is shared across all callers in the org. Plan
        accordingly before running backfills or automated pipelines.

        NOTE on return shape: returns a wide-format DataFrame, which differs
        from get_recent_measurements()'s json-long format. One row per
        (datasource, time-period). The timestamp column is named 'startOfPeriod'.
        Metric value columns follow the pattern '{metricName}.value' (e.g.
        'pm2_5ConcMass1HourMean.value'), with a paired '{metricName}.raw' where
        the sensor provides a raw reading alongside the calibrated value.

        Args:
            start_time: Required. ISO 8601 string or datetime. Inclusive lower bound.
            end_time: Required. ISO 8601 string or datetime. Exclusive upper bound.
            datasource_ids: List of datasource ID strings. Mutually exclusive with
                all_datasources. Defaults to all datasources if omitted.
            all_datasources: If True, query all org datasources.
            output_frequency: 'minute', 'hour' (default), or 'day'.
            metric_select: Optional metric filter string.
            file_format: 'csv' (default), 'csv-wide', 'parquet', or 'parquet-wide'.
            metric_label_style: 'canonical' (default), 'english', or 'legacy'.
            poll_interval: Seconds between status checks after the first poll.
                Default 15. First poll always occurs after min(10, poll_interval)
                seconds to handle fast reports without unnecessary waiting.
            timeout: Max seconds to wait for report completion. Default 600.

        Returns:
            pandas.DataFrame in wide format (see shape note above), or None on
            error, rate-limit (429), or timeout.
        """
        url = f"{self.base_url}report-requests"
        body = {
            "org": self.org,
            "report": "datasource-measurements",
            "outputFrequency": output_frequency,
            "startTime": self._format_time(start_time),
            "endTime": self._format_time(end_time),
            "fileFormat": file_format,
            "metricLabelStyle": metric_label_style,
        }
        body.update(self._resolve_datasource_params(datasource_ids, all_datasources))
        if metric_select is not None:
            body["metricSelect"] = metric_select

        try:
            response = requests.post(url, headers=self.headers, json=body)
            if response.status_code == 429:
                print(
                    "Rate limit reached: 30 historical measurement reports per organization "
                    "per day. Resets at UTC midnight."
                )
                return None
            response.raise_for_status()
        except requests.exceptions.HTTPError as err:
            print(f"HTTP error occurred: {err}")
            return None
        except Exception as err:
            print(f"An error occurred: {err}")
            return None

        report_id = response.json().get("reportId")
        if not report_id:
            print(f"Unexpected response: no reportId returned. Response: {response.json()}")
            return None

        print(f"Report submitted (id: {report_id}). Polling for completion...")
        elapsed = 0
        wait = min(10, poll_interval)  # first poll is short; subsequent polls use poll_interval
        while elapsed < timeout:
            time.sleep(wait)
            elapsed += wait
            wait = poll_interval
            status = self._get_report_status(report_id)
            if status is None:
                return None
            report_status = status.get("reportStatus")
            print(f"  Status: {report_status} ({elapsed}s elapsed)")
            if report_status == "succeeded":
                urls = status.get("urls", [])
                if not urls:
                    print("Report succeeded but no download URLs returned.")
                    return None
                return self._download_report(urls, file_format)
            elif report_status == "failed":
                print(f"Report failed. Details: {status.get('message', 'no message')}")
                return None

        print(f"Timed out waiting for report after {timeout}s.")
        return None

    def _get_report_status(self, report_id):
        """Check the status of a submitted report request.

        Args:
            report_id: Report ID string returned when a report was submitted.

        Returns:
            dict with at least 'reportStatus' and 'urls' fields, or None on error.
        """
        url = f"{self.base_url}report-requests/{report_id}"
        params = {"org": self.org}
        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as err:
            print(f"HTTP error occurred: {err}")
            return None
        except Exception as err:
            print(f"An error occurred: {err}")
            return None

    def _download_report(self, urls, file_format):
        frames = []
        for url in urls:
            try:
                response = requests.get(url)
                response.raise_for_status()
                if file_format in ("parquet", "parquet-wide"):
                    frames.append(pd.read_parquet(io.BytesIO(response.content)))
                else:
                    frames.append(pd.read_csv(io.StringIO(response.text)))
            except Exception as err:
                print(f"Error downloading report file: {err}")
                return None
        if not frames:
            return None
        return pd.concat(frames, ignore_index=True) if len(frames) > 1 else frames[0]

    def get_datasources(self):
        """Fetch all datasources for the organization.

        Returns:
            dict with 'datasources' key containing a list of datasource objects,
            or None on error.
        """
        url = f"{self.base_url}datasources"
        params = {"org": self.org}
        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as err:
            print(f"HTTP error occurred: {err}")
        except Exception as err:
            print(f"An error occurred: {err}")

    def get_datasource_details(self, datasource_id):
        """Fetch details for a specific datasource.

        Args:
            datasource_id: The datasource ID string.

        Returns:
            dict with 'datasource' key, or None on error.
        """
        url = f"{self.base_url}datasources/{datasource_id}"
        params = {"org": self.org}
        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as err:
            print(f"HTTP error occurred: {err}")
        except Exception as err:
            print(f"An error occurred: {err}")
