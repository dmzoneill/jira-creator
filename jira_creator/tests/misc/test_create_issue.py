from jira.client import JiraClient


def test_create_issue(monkeypatch):
    client = JiraClient()
    monkeypatch.setattr(client, "_request", lambda *a, **kw: {"key": "AAP-1"})
    key = client.create_issue({"fields": {"summary": "Test"}})
    assert key == "AAP-1"
