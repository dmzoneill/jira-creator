from jira.client import JiraClient
import requests


def test_empty_text_response(monkeypatch):
    class MockResponse:
        status_code = 200
        text = "  "

    monkeypatch.setattr(requests, "request", lambda *a, **k: MockResponse())
    c = JiraClient()
    result = c._request("GET", "/x")
    assert result == {}
