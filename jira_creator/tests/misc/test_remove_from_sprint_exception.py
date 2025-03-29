from jira.client import JiraClient


def test_remove_from_sprint_error(monkeypatch, capsys):
    client = JiraClient()
    monkeypatch.setattr(
        client, "_request", lambda *a, **k: (_ for _ in ()).throw(Exception("fail"))
    )
    client.remove_from_sprint("AAP-1")
    out = capsys.readouterr().out
    assert "❌ Failed to remove from sprint" in out
