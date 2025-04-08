from unittest.mock import MagicMock

import pytest
from exceptions.exceptions import ViewIssueError


def test_view_issue(cli, capsys):
    blob = {"smokekey": "somevalue", "customfield_12345": 3}

    cli.jira.get_field_name = MagicMock(return_value="xxx")
    cli.jira.view_issue = MagicMock(return_value=blob)

    class Args:
        issue_key = "AAP-test_view_issue"

    # Call the handle function
    cli.view_issue(Args())

    # Capture the printed output
    # captured = capsys.readouterr()

    # Assert that the correct message was printed
    # assert "✅ Story's epic set to 'EPIC-123'" in captured.out

    # Ensure that set_story_epic was called with the correct arguments
    cli.jira.view_issue.assert_called_once_with("AAP-test_view_issue")


def test_view_issue_exception(cli, capsys):
    cli.jira.view_issue = MagicMock(side_effect=ViewIssueError("fail"))

    class Args:
        issue_key = "AAP-test_view_issue_exception"

    with pytest.raises(ViewIssueError):
        # Call the handle function
        cli.view_issue(Args())

    captured = capsys.readouterr()

    # Assert that the correct error message was printed
    assert "❌ Unable to view issue: fail" in captured.out

    # Ensure that set_story_epic was called with the correct arguments
    cli.jira.view_issue.assert_called_once_with("AAP-test_view_issue_exception")
