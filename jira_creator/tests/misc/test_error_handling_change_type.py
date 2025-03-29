from jira.client import JiraClient
import pytest


def test_change_issue_type_fails(monkeypatch):
    client = JiraClient()
    monkeypatch.setattr(
        client, "_request", lambda *a, **k: (_ for _ in ()).throw(Exception("failure"))
    )
    success = client.change_issue_type("AAP-1", "task")
    assert not success
