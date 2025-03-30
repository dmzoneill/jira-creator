from jira.client import JiraClient
from unittest.mock import MagicMock


def test_request_allow_204():
    client = JiraClient()

    # Create a mock response object
    mock_response = MagicMock()
    mock_response.status_code = 204
    mock_response.text = ""

    # Mock requests.request to return the mocked response
    with MagicMock() as mock_request:
        mock_request.return_value = mock_response
        client._request = mock_request
        
        result = client._request("GET", "/fake", allow_204=True)
        assert result == {}


def test_request_json_return():
    client = JiraClient()

    # Create a mock response object
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = "ok"
    mock_response.json.return_value = {"ok": True}

    # Mock the _request method to return the mock response
    with MagicMock() as mock_request:
        mock_request.return_value = mock_response
        client._request = mock_request  # Assign the mock to client._request

        # Call the _request method
        result = client._request("GET", "/fake")

        # Check that the result returned from the mock is the expected JSON
        assert result == {"ok": True}
