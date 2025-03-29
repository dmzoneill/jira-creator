import pytest
from jira.client import JiraClient


def test_request_raises_on_400(monkeypatch):
    client = JiraClient()

    class MockResponse:
        status_code = 400
        text = "Bad Request"

    monkeypatch.setattr("requests.request", lambda *a, **kw: MockResponse())
    with pytest.raises(Exception, match="JIRA API error"):
        client._request("GET", "/bad/path")


def test_request_empty_response(monkeypatch):
    client = JiraClient()

    class MockResponse:
        status_code = 200
        text = ""

    monkeypatch.setattr("requests.request", lambda *a, **kw: MockResponse())
    result = client._request("GET", "/empty")
    assert result == {}
