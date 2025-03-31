from unittest.mock import MagicMock

import pytest
from jira.client import JiraClient


@pytest.fixture
def client():
    client = JiraClient()
    client.list_issues = MagicMock()
    return client


def test_get_blocked_issues_found(client):
    client.list_issues.return_value = [
        {
            "key": "AAP-123",
            "fields": {
                "summary": "Fix DB timeout",
                "status": {"name": "In Progress"},
                "assignee": {"displayName": "Alice"},
                "customfield_12316543": {"value": "True"},
                "customfield_12316544": "DB down",
            },
        }
    ]

    result = client.blocked()
    assert len(result) == 1
    assert result[0]["key"] == "AAP-123"
    assert result[0]["reason"] == "DB down"


def test_get_blocked_issues_none_blocked(client):
    client.list_issues.return_value = [
        {
            "key": "AAP-999",
            "fields": {
                "summary": "Write docs",
                "status": {"name": "To Do"},
                "assignee": {"displayName": "Bob"},
                "customfield_12316543": {"value": "False"},
                "customfield_12316544": "",
            },
        }
    ]
    result = client.blocked()
    assert result == []


def test_get_blocked_issues_no_issues(client):
    client.list_issues.return_value = []
    result = client.blocked()
    assert result == []


def test_get_blocked_issues_exception():
    client = JiraClient()
    client.list_issues = MagicMock(side_effect=Exception("Simulated list failure"))

    with pytest.raises(Exception, match="Simulated list failure"):
        client.blocked()
