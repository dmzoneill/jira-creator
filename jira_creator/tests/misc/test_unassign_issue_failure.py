from jira.client import JiraClient


def test_unassign_issue_fails(monkeypatch, capsys):
    client = JiraClient()
    monkeypatch.setattr(
        client, "_request", lambda *a, **k: (_ for _ in ()).throw(Exception("fail"))
    )
    result = client.unassign_issue("AAP-999")
    assert not result
    assert "❌ Failed to unassign issue" in capsys.readouterr().out
