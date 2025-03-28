import pytest
from unittest.mock import MagicMock
from jira.client import JiraClient


def test_set_status_transitions(monkeypatch):
    client = JiraClient()
    monkeypatch.setattr(client, "_request", MagicMock())
    transitions = {"transitions": [{"name": "In Progress", "id": "31"}]}
    client._request.side_effect = [transitions, {}]  # GET then POST
    client.set_status("AAP-1", "In Progress")
    assert client._request.call_count == 2
