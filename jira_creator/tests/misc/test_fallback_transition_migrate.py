from jira.client import JiraClient
import pytest


def test_migrate_fallback_transition(monkeypatch):
    client = JiraClient()

    def mock_request(method, path, **kwargs):
        if path == "/rest/api/2/issue/AAP-1":
            return {
                "fields": {"summary": "Old summary", "description": "Old desc"},
                "key": "AAP-1",
            }
        elif method == "POST" and path == "/rest/api/2/issue/":
            return {"key": "AAP-2"}
        elif "/comment" in path:
            return {}
        elif "/transitions" in path:
            return {"transitions": [{"id": "5", "name": "Some Status"}]}

    monkeypatch.setattr(client, "_request", mock_request)
    monkeypatch.setattr(client, "jira_url", "http://fake")

    new_key = client.migrate_issue("AAP-1", "story")
    assert new_key == "AAP-2"
