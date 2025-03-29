from jira.client import JiraClient


def test_unassign_issue(monkeypatch):
    client = JiraClient()
    monkeypatch.setattr(client, "_request", lambda *a, **kw: {})
    result = client.unassign_issue("AAP-100")
    assert result is True
