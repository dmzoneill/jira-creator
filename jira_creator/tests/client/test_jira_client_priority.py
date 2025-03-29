from unittest.mock import MagicMock

from jira.client import JiraClient


def test_set_priority(monkeypatch):
    client = JiraClient()
    monkeypatch.setattr(client, "_request", MagicMock())
    client.set_priority("AAP-123", "High")
    client._request.assert_called_once()
