import io
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
import requests

from clarityio.clarityio import ClarityAPIConnection


@pytest.fixture
def conn():
    return ClarityAPIConnection(api_key="test-key", org="test-org")


# ---------------------------------------------------------------------------
# _resolve_datasource_params
# ---------------------------------------------------------------------------

def test_resolve_all_datasources(conn):
    assert conn._resolve_datasource_params(None, None) == {"allDatasources": True}
    assert conn._resolve_datasource_params(None, True) == {"allDatasources": True}


def test_resolve_datasource_ids(conn):
    result = conn._resolve_datasource_params(["DS1", "DS2"], None)
    assert result == {"datasourceIds": ["DS1", "DS2"]}


def test_resolve_conflict_raises(conn):
    with pytest.raises(ValueError):
        conn._resolve_datasource_params(["DS1"], True)


# ---------------------------------------------------------------------------
# get_recent_measurements
# ---------------------------------------------------------------------------

def _mock_post(json_data=None, status_code=200, headers=None):
    response = MagicMock()
    response.status_code = status_code
    response.json.return_value = json_data or {}
    response.text = "csv,data"
    response.headers = headers or {}
    if status_code >= 400:
        response.raise_for_status.side_effect = requests.exceptions.HTTPError(
            response=response
        )
    else:
        response.raise_for_status.return_value = None
    return response


@patch("clarityio.clarityio.requests.post")
def test_get_recent_default_all_datasources(mock_post, conn):
    mock_post.return_value = _mock_post({"measurements": []})
    result = conn.get_recent_measurements()
    assert result == {"measurements": []}
    body = mock_post.call_args[1]["json"]
    assert body["allDatasources"] is True
    assert body["outputFrequency"] == "hour"
    assert body["org"] == "test-org"


@patch("clarityio.clarityio.requests.post")
def test_get_recent_single_datasource(mock_post, conn):
    mock_post.return_value = _mock_post({"measurements": []})
    conn.get_recent_measurements(datasource_ids=["DGLTC1243"])
    body = mock_post.call_args[1]["json"]
    assert body["datasourceIds"] == ["DGLTC1243"]
    assert "allDatasources" not in body


@patch("clarityio.clarityio.requests.post")
def test_get_recent_csv_format(mock_post, conn):
    mock_post.return_value = _mock_post(status_code=200)
    result = conn.get_recent_measurements(format="csv-wide")
    assert result == "csv,data"


@patch("clarityio.clarityio.requests.post")
def test_get_recent_with_continuation_token(mock_post, conn):
    mock_post.return_value = _mock_post(
        {"measurements": []},
        headers={"x-clarity-continuation-token": "tok123"},
    )
    data, token = conn.get_recent_measurements(reply_with_continuation_token=True)
    assert data == {"measurements": []}
    assert token == "tok123"
    body = mock_post.call_args[1]["json"]
    assert body["replyWithContinuationToken"] is True


@patch("clarityio.clarityio.requests.post")
def test_get_recent_http_error_returns_none(mock_post, conn):
    mock_post.return_value = _mock_post(status_code=400)
    assert conn.get_recent_measurements() is None


@patch("clarityio.clarityio.requests.post")
def test_get_recent_http_error_returns_none_tuple_with_token(mock_post, conn):
    mock_post.return_value = _mock_post(status_code=400)
    result = conn.get_recent_measurements(reply_with_continuation_token=True)
    assert result == (None, None)


@patch("clarityio.clarityio.requests.post")
def test_get_recent_deprecated_data_param(mock_post, conn):
    mock_post.return_value = _mock_post({"data": []})
    with pytest.warns(DeprecationWarning, match="data.*deprecated"):
        result = conn.get_recent_measurements(
            data={"allDatasources": True, "outputFrequency": "hour", "format": "json-long"}
        )
    assert result == {"data": []}
    body = mock_post.call_args[1]["json"]
    assert body["org"] == "test-org"
    assert body["allDatasources"] is True


@patch("clarityio.clarityio.requests.post")
def test_get_recent_deprecated_data_param_csv(mock_post, conn):
    mock_post.return_value = _mock_post(status_code=200)
    with pytest.warns(DeprecationWarning):
        result = conn.get_recent_measurements(data={"format": "csv-wide"})
    assert result == "csv,data"


@patch("clarityio.clarityio.requests.post")
def test_get_recent_deprecated_data_param_error(mock_post, conn):
    mock_post.return_value = _mock_post(status_code=500)
    with pytest.warns(DeprecationWarning):
        result = conn.get_recent_measurements(data={"allDatasources": True})
    assert result is None


# ---------------------------------------------------------------------------
# get_measurements_continuation
# ---------------------------------------------------------------------------

@patch("clarityio.clarityio.requests.post")
def test_get_measurements_continuation_success(mock_post, conn):
    mock_post.return_value = _mock_post(
        {"measurements": [1, 2]},
        headers={"x-clarity-continuation-token": "tok456"},
    )
    data, new_token = conn.get_measurements_continuation("tok123")
    assert data == {"measurements": [1, 2]}
    assert new_token == "tok456"
    body = mock_post.call_args[1]["json"]
    assert body["continuationToken"] == "tok123"
    assert body["org"] == "test-org"


@patch("clarityio.clarityio.requests.post")
def test_get_measurements_continuation_error(mock_post, conn):
    mock_post.return_value = _mock_post(status_code=401)
    data, token = conn.get_measurements_continuation("bad-token")
    assert data is None
    assert token is None


# ---------------------------------------------------------------------------
# get_historical_measurements
# ---------------------------------------------------------------------------

def _mock_get(json_data=None, status_code=200):
    response = MagicMock()
    response.status_code = status_code
    response.json.return_value = json_data or {}
    response.text = "ts,value\n2024-04-01,1.0\n"
    response.content = b"parquet-bytes"
    response.headers = {}
    if status_code >= 400:
        response.raise_for_status.side_effect = requests.exceptions.HTTPError(
            response=response
        )
    else:
        response.raise_for_status.return_value = None
    return response


@patch("clarityio.clarityio.time.sleep")
@patch("clarityio.clarityio.requests.get")
@patch("clarityio.clarityio.requests.post")
def test_get_historical_success(mock_post, mock_get, mock_sleep, conn):
    mock_post.return_value = _mock_post({"reportId": "rpt-1"})
    mock_get.side_effect = [
        _mock_get({"reportStatus": "in-progress"}),
        _mock_get({"reportStatus": "succeeded", "urls": ["https://example.com/data.csv"]}),
        # Third call: download the CSV
        _mock_get(),
    ]

    result = conn.get_historical_measurements(
        start_time="2024-04-01T00:00:00Z",
        end_time="2024-04-08T00:00:00Z",
    )

    assert isinstance(result, pd.DataFrame)
    assert list(result.columns) == ["ts", "value"]
    # Confirm body sent to report-requests
    body = mock_post.call_args[1]["json"]
    assert body["startTime"] == "2024-04-01T00:00:00Z"
    assert body["endTime"] == "2024-04-08T00:00:00Z"
    assert body["allDatasources"] is True
    assert body["report"] == "datasource-measurements"


@patch("clarityio.clarityio.time.sleep")
@patch("clarityio.clarityio.requests.get")
@patch("clarityio.clarityio.requests.post")
def test_get_historical_single_datasource(mock_post, mock_get, mock_sleep, conn):
    mock_post.return_value = _mock_post({"reportId": "rpt-2"})
    mock_get.side_effect = [
        _mock_get({"reportStatus": "succeeded", "urls": ["https://example.com/data.csv"]}),
        _mock_get(),
    ]

    conn.get_historical_measurements(
        start_time="2024-04-01T00:00:00Z",
        end_time="2024-04-08T00:00:00Z",
        datasource_ids=["DGLTC1243"],
    )

    body = mock_post.call_args[1]["json"]
    assert body["datasourceIds"] == ["DGLTC1243"]
    assert "allDatasources" not in body


@patch("clarityio.clarityio.requests.post")
def test_get_historical_rate_limit(mock_post, conn):
    mock_post.return_value = _mock_post(status_code=429)
    mock_post.return_value.raise_for_status.side_effect = None  # 429 handled before raise_for_status
    result = conn.get_historical_measurements(
        start_time="2024-04-01T00:00:00Z",
        end_time="2024-04-08T00:00:00Z",
    )
    assert result is None


@patch("clarityio.clarityio.time.sleep")
@patch("clarityio.clarityio.requests.get")
@patch("clarityio.clarityio.requests.post")
def test_get_historical_report_failed(mock_post, mock_get, mock_sleep, conn):
    mock_post.return_value = _mock_post({"reportId": "rpt-3"})
    mock_get.return_value = _mock_get(
        {"reportStatus": "failed", "message": "internal error"}
    )
    result = conn.get_historical_measurements(
        start_time="2024-04-01T00:00:00Z",
        end_time="2024-04-08T00:00:00Z",
        poll_interval=1,
        timeout=2,
    )
    assert result is None


@patch("clarityio.clarityio.time.sleep")
@patch("clarityio.clarityio.requests.get")
@patch("clarityio.clarityio.requests.post")
def test_get_historical_timeout(mock_post, mock_get, mock_sleep, conn):
    mock_post.return_value = _mock_post({"reportId": "rpt-4"})
    mock_get.return_value = _mock_get({"reportStatus": "in-progress"})
    result = conn.get_historical_measurements(
        start_time="2024-04-01T00:00:00Z",
        end_time="2024-04-08T00:00:00Z",
        poll_interval=5,
        timeout=8,
    )
    assert result is None


@patch("clarityio.clarityio.time.sleep")
@patch("clarityio.clarityio.requests.get")
@patch("clarityio.clarityio.requests.post")
def test_get_historical_multiple_files_concatenated(mock_post, mock_get, mock_sleep, conn):
    mock_post.return_value = _mock_post({"reportId": "rpt-5"})
    csv1 = "ts,value\n2024-04-01,1.0\n"
    csv2 = "ts,value\n2024-04-02,2.0\n"

    status_response = _mock_get(
        {"reportStatus": "succeeded", "urls": ["https://example.com/f1.csv", "https://example.com/f2.csv"]}
    )
    dl1 = MagicMock()
    dl1.raise_for_status.return_value = None
    dl1.text = csv1
    dl2 = MagicMock()
    dl2.raise_for_status.return_value = None
    dl2.text = csv2

    mock_get.side_effect = [status_response, dl1, dl2]

    result = conn.get_historical_measurements(
        start_time="2024-04-01T00:00:00Z",
        end_time="2024-04-03T00:00:00Z",
    )

    assert len(result) == 2
    assert list(result["value"]) == [1.0, 2.0]


# ---------------------------------------------------------------------------
# get_datasources / get_datasource_details
# ---------------------------------------------------------------------------

@patch("clarityio.clarityio.requests.get")
def test_get_datasources(mock_get, conn):
    mock_get.return_value = _mock_get({"datasources": [{"id": "DS1"}]})
    result = conn.get_datasources()
    assert result["datasources"][0]["id"] == "DS1"
    params = mock_get.call_args[1]["params"]
    assert params["org"] == "test-org"


@patch("clarityio.clarityio.requests.get")
def test_get_datasource_details(mock_get, conn):
    mock_get.return_value = _mock_get({"datasource": {"id": "DS1", "name": "Station"}})
    result = conn.get_datasource_details("DS1")
    assert result["datasource"]["name"] == "Station"
    assert "DS1" in mock_get.call_args[0][0]
