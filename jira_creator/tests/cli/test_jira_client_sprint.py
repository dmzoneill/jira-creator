import pytest
from unittest.mock import MagicMock
from jira.client import JiraClient


def test_set_sprint(monkeypatch):
    client = JiraClient()
    monkeypatch.setattr(client, "_request", MagicMock())
    client.set_sprint("AAP-123", 42)
    client._request.assert_called_once()


def test_remove_from_sprint(monkeypatch):
    client = JiraClient()
    monkeypatch.setattr(client, "_request", MagicMock())
    client.remove_from_sprint("AAP-123")
    client._request.assert_called_once()
