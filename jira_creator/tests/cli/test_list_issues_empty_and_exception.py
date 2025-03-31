from unittest.mock import MagicMock

from jira_creator.rh_jira import JiraCLI


def test_list_issues_empty(capsys):
    cli = JiraCLI()

    # Mock list_issues to return an empty list
    cli.jira.list_issues = MagicMock(return_value=[])

    class Args:
        project = None
        component = None
        user = None

    cli.list_issues(Args())
    out = capsys.readouterr().out
    assert "No issues found." in out


def test_list_issues_fail(capsys):
    cli = JiraCLI()

    # Mock list_issues to raise an exception
    cli.jira.list_issues = MagicMock(side_effect=Exception("fail"))

    class Args:
        project = None
        component = None
        user = None

    cli.list_issues(Args())
    out = capsys.readouterr().out
    assert "❌ Failed to list issues" in out
