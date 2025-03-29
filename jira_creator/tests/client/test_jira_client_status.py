from unittest.mock import MagicMock

from jira.client import JiraClient


def test_set_status(monkeypatch):
    client = JiraClient()
    monkeypatch.setattr(client, "_request", MagicMock())
    client._request.side_effect = [{"transitions": [{"name": "Done", "id": "2"}]}, {}]
    client.set_status("AAP-123", "Done")
    assert client._request.call_count == 2
