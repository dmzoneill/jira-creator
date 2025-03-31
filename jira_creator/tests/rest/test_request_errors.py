from unittest.mock import patch

import pytest
from jira.client import JiraClient


def test_request_raises_on_400():
    client = JiraClient()

    class MockResponse:
        status_code = 400
        text = "Bad Request"

    with patch("requests.request", return_value=MockResponse()):
        with pytest.raises(Exception, match="JIRA API error"):
            client._request("GET", "/bad/path")


def test_request_empty_response():
    client = JiraClient()

    class MockResponse:
        status_code = 200
        text = ""

    with patch("requests.request", return_value=MockResponse()):
        result = client._request("GET", "/empty")
        assert result == {}
