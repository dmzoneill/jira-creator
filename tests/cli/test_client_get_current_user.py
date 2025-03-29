from jira.client import JiraClient


def test_get_current_user(monkeypatch):
    client = JiraClient()
    monkeypatch.setattr(client, "_request", lambda *a, **k: {"name": "user123"})
    assert client.get_current_user() == "user123"
