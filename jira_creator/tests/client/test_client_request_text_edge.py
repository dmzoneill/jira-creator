from unittest.mock import patch

from jira.client import JiraClient


def test_empty_text_response():
    class MockResponse:
        status_code = 200
        text = "  "  # Only whitespace

    with patch("requests.request", return_value=MockResponse()):
        client = JiraClient()
        result = client._request("GET", "/x")
        assert result == {}
