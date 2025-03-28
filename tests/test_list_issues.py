import pytest
from unittest.mock import MagicMock
from rh_jira import JiraCLI


def test_list_issues_format(monkeypatch):
    cli = JiraCLI()
    cli.jira.list_issues = MagicMock(
        return_value=[
            {
                "key": "AAP-1",
                "fields": {
                    "summary": "Test Summary",
                    "status": {"name": "To Do"},
                    "assignee": {"displayName": "Alice"},
                    "priority": {"name": "High"},
                    "customfield_12310243": 5,
                    "customfield_12310940": ["state=ACTIVE,name=Sprint 1"],
                },
            }
        ]
    )
    monkeypatch.setattr("builtins.print", lambda x: None)  # Suppress output
    cli.list_issues(
        args=type("Args", (), {"project": None, "component": None, "user": None})
    )
    assert cli.jira.list_issues.called
