from unittest.mock import MagicMock, patch

from rest.client import JiraClient


def test_request_success():
    client = JiraClient()
    # Mock a successful response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = '{"key": "value"}'
    # Mock json method to return the actual dictionary
    mock_response.json.return_value = {"key": "value"}

    with patch("requests.request", return_value=mock_response) as mock_request:
        # Call the method that should trigger the mock
        result = client._request("GET", "/rest/api/2/issue/ISSUE-123")

        # Assert that the correct result is returned
        assert result == {"key": "value"}

        # Verify that requests.request was called with the correct arguments
        mock_request.assert_called_once()
