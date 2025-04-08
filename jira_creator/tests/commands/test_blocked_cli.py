from unittest.mock import MagicMock

import pytest
from core.env_fetcher import EnvFetcher
from exceptions.exceptions import ListBlockedError


class Args:
    project = None
    component = None
    user = None


def test_blocked_issues_found(cli, capsys):
    cli.jira = MagicMock()

    cli.jira.list_issues.return_value = [
        {
            "key": "AAP-test_blocked_issues_found-0",
            "fields": {
                "status": {"name": "In Progress"},
                "assignee": {"displayName": "Jane"},
                EnvFetcher.get("JIRA_BLOCKED_FIELD"): {"value": "True"},
                EnvFetcher.get("JIRA_BLOCKED_REASON_FIELD"): "Waiting for DB",
                "summary": "Fix DB timeout issue",
            },
        },
        {
            "key": "AAP-test_blocked_issues_found-1",
            "fields": {
                "status": {"name": "Ready"},
                "assignee": {"displayName": "John"},
                EnvFetcher.get("JIRA_BLOCKED_FIELD"): {"value": "False"},
                EnvFetcher.get("JIRA_BLOCKED_REASON_FIELD"): "",
                "summary": "Update readme",
            },
        },
    ]

    cli.blocked(Args())

    out = capsys.readouterr().out
    assert "🔒 Blocked issues:" in out
    assert "AAP-test_blocked_issues_found-0" in out
    assert "Waiting for DB" in out
    assert "AAP-test_blocked_issues_found-1" not in out


def test_blocked_no_issues(cli, capsys):
    cli.jira = MagicMock()
    cli.jira.list_issues.return_value = []

    cli.blocked(Args())

    out = capsys.readouterr().out
    assert "✅ No issues found." in out


def test_blocked_none_blocked(cli, capsys):
    cli.jira = MagicMock()
    cli.jira.list_issues.return_value = [
        {
            "key": "AAP-test_blocked_none_blocked",
            "fields": {
                "summary": "Add tests",
                "status": {"name": "To Do"},
                "assignee": {"displayName": "Alex"},
                EnvFetcher.get("JIRA_BLOCKED_FIELD"): {"value": "False"},
                EnvFetcher.get("JIRA_BLOCKED_REASON_FIELD"): "",
            },
        }
    ]

    cli.blocked(Args())
    out = capsys.readouterr().out
    assert "✅ No blocked issues found." in out
    assert "AAP-test_blocked_none_blocked" not in out


def test_blocked_exception(cli, capsys):
    cli.jira = MagicMock()
    cli.jira.list_issues.side_effect = ListBlockedError("Boom!")

    with pytest.raises(ListBlockedError):
        cli.blocked(Args())

    out = capsys.readouterr().out
    assert "❌ Failed to list blocked issues" in out
