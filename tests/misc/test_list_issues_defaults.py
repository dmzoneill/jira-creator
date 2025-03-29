from jira.client import JiraClient


def test_list_issues_defaults(monkeypatch):
    client = JiraClient()
    monkeypatch.setattr(client, "get_current_user", lambda: "me")
    monkeypatch.setattr(client, "_request", lambda *a, **k: {"issues": []})
    result = client.list_issues()
    assert result == []
