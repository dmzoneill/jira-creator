from unittest.mock import MagicMock

import pytest
from exceptions.exceptions import ListIssuesError


def test_list_issues_empty(cli, capsys):
    # Mock list_issues to return an empty list
    cli.jira.list_issues = MagicMock(return_value=[])

    class Args:
        project = None
        component = None
        user = None
        assignee = None
        reporter = None

    cli.list_issues(Args())
    out = capsys.readouterr().out
    assert "No issues found." in out


def test_list_issues_fail(cli, capsys):
    # Mock list_issues to raise an exception
    cli.jira.list_issues = MagicMock(side_effect=ListIssuesError("fail"))

    class Args:
        project = None
        component = None
        assignee = None
        reporter = None

    with pytest.raises(ListIssuesError):
        cli.list_issues(Args())

    out = capsys.readouterr().out
    assert "❌ Failed to list issues" in out
