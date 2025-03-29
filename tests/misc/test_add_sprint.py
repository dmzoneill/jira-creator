import pytest
from unittest.mock import MagicMock
from jira.client import JiraClient


def test_add_to_sprint_by_name_success(monkeypatch):
    monkeypatch.setenv("JIRA_BOARD_ID", "123")
    client = JiraClient()
    client._request = MagicMock()
    client._request.side_effect = [
        {"values": [{"id": 88, "name": "Sprint 42"}]},  # Sprint lookup
        {},  # Assignment
    ]
    client.add_to_sprint_by_name("AAP-1", "Sprint 42")
    assert client._request.call_count == 2


def test_add_to_sprint_by_name_not_found(monkeypatch):
    monkeypatch.setenv("JIRA_BOARD_ID", "123")
    client = JiraClient()
    client._request = MagicMock(return_value={"values": []})
    with pytest.raises(Exception) as exc:
        client.add_to_sprint_by_name("AAP-1", "Nonexistent Sprint")
    assert "Could not find sprint" in str(exc.value)
