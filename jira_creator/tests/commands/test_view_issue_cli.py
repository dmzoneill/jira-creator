"""
This script contains unit tests for the view_issue function in the cli module. It uses MagicMock to mock certain
functionalities and pytest for testing exceptions. The tests validate the behavior of viewing an issue and handling
exceptions when viewing an issue fails. The tests verify that the correct messages are printed and the expected
functions are called with the appropriate arguments.
"""

from unittest.mock import MagicMock

import pytest
from exceptions.exceptions import ViewIssueError


def test_view_issue(cli, capsys):
    """
    Simulate a test scenario for viewing an issue.

    Arguments:
    - cli: An object representing the command line interface for testing.
    - capsys: An object to capture stdout and stderr during testing.

    Side Effects:
    - Initializes a dictionary 'blob' with key-value pairs representing issue details.

    """

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
    """
    Simulate an exception when viewing an issue in Jira for testing purposes.

    Arguments:
    - cli: The Jira command line interface object.
    - capsys: The pytest fixture for capturing stdout and stderr.

    Exceptions:
    - ViewIssueError: Raised when there is a failure while viewing an issue in Jira.

    """

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
