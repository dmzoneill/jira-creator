from unittest.mock import MagicMock, patch

from exceptions.exceptions import JiraClientRequestError
from rest.client import JiraClient


def test_request_success_valid_json():
    client = JiraClient()

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = '{"key": "value"}'
    mock_response.json.return_value = {"key": "value"}

    with patch(
        "rest.client.requests.request", return_value=mock_response
    ) as mock_request:
        result = client._request("GET", "/rest/api/2/issue/ISSUE-123")
        assert result == {"key": "value"}
        mock_request.assert_called_once()


def test_request_empty_response_text():
    client = JiraClient()

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = ""
    mock_response.json.return_value = {}  # shouldn't be called

    with patch(
        "rest.client.requests.request", return_value=mock_response
    ) as mock_request:
        result = client._request("GET", "/rest/api/2/issue/ISSUE-EMPTY")
        assert result == {}
        mock_request.assert_called_once()


def test_request_invalid_json_response():
    client = JiraClient()

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = "<html>This is not JSON</html>"
    mock_response.json.side_effect = ValueError("No JSON")

    with patch(
        "rest.client.requests.request", return_value=mock_response
    ) as mock_request:
        result = client._request("GET", "/rest/api/2/issue/ISSUE-BADJSON")
        assert result == {}  # falls back to empty dict
        mock_request.assert_called()


def test_request_with_retry_and_failure():
    client = JiraClient()

    with patch(
        "requests.request", side_effect=JiraClientRequestError("Network down")
    ) as mock_request:
        with patch("time.sleep", return_value=None) as mock_sleep:
            try:
                client._request("GET", "/rest/api/2/issue/ISSUE-FAIL")
            except JiraClientRequestError as e:
                assert "Network down" in str(e)

            # Should retry 3 times (initial try + 2 retries)
            assert mock_request.call_count == 3
            assert mock_sleep.call_count == 2
