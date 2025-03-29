from jira.client import JiraClient
import pytest


def test_status_transition_missing(monkeypatch):
    client = JiraClient()
    monkeypatch.setattr(client, "_request", lambda *a, **k: {"transitions": []})
    with pytest.raises(Exception, match="Transition to status 'done' not found"):
        client.set_status("AAP-1", "done")
