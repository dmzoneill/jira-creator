from jira.client import JiraClient


def test_get_update_description(monkeypatch):
    client = JiraClient()
    monkeypatch.setattr(
        client, "_request", lambda *a, **k: {"fields": {"description": "text"}}
    )
    desc = client.get_description("AAP-1")
    assert desc == "text"

    updated = {}
    monkeypatch.setattr(
        client, "_request", lambda *a, **k: updated.update(k.get("json", {}))
    )
    client.update_description("AAP-1", "new text")
    assert "description" in updated["fields"]
