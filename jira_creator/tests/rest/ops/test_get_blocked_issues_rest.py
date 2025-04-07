from unittest.mock import MagicMock

import pytest
from core.env_fetcher import EnvFetcher


def test_get_blocked_issues_found(client):
    client.list_issues = MagicMock(
        return_value=[
            {
                "key": "AAP-test_get_blocked_issues_found",
                "fields": {
                    "summary": "Fix DB timeout",
                    "status": {"name": "In Progress"},
                    "assignee": {"displayName": "Alice"},
                    EnvFetcher.get("JIRA_BLOCKED_FIELD"): {"value": "True"},
                    EnvFetcher.get("JIRA_BLOCKED_REASON_FIELD"): "DB down",
                },
            }
        ]
    )

    result = client.blocked()
    assert len(result) == 1
    assert result[0]["key"] == "AAP-test_get_blocked_issues_found"
    assert result[0]["reason"] == "DB down"


def test_get_blocked_issues_none_blocked(client):
    client.list_issues = MagicMock(
        return_value=[
            {
                "key": "AAP-test_get_blocked_issues_none_blocked",
                "fields": {
                    "summary": "Write docs",
                    "status": {"name": "To Do"},
                    "assignee": {"displayName": "Bob"},
                    EnvFetcher.get("JIRA_BLOCKED_FIELD"): {"value": "False"},
                    EnvFetcher.get("JIRA_BLOCKED_REASON_FIELD"): "",
                },
            }
        ]
    )
    result = client.blocked()
    assert len(result) == 0


def test_get_blocked_issues_no_issues(client):
    client.list_issues = MagicMock(return_value=[])
    result = client.blocked()
    assert result == []


def test_get_blocked_issues_exception(client):
    client.list_issues = MagicMock(side_effect=Exception("Simulated list failure"))

    with pytest.raises(Exception, match="Simulated list failure"):
        client.blocked()
