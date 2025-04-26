#!/usr/bin/env python
"""
This module contains unit tests for the `view_issue` function within the `cli` module. It utilizes `pytest` for testing
and `MagicMock` to simulate interactions with the Jira API. The tests cover both successful and exceptional scenarios
of viewing an issue, ensuring that correct outputs are produced and appropriate methods are invoked with expected
arguments.

Functions:
- `test_view_issue(cli, capsys)`: Tests the successful retrieval of an issue.
- `test_view_issue_exception(cli, capsys)`: Tests the handling of exceptions when attempting to view an issue.

Arguments:
- `cli`: An instance of the command line interface used for testing.
- `capsys`: A pytest fixture that captures standard output and error streams.

Exceptions:
- `ViewIssueError`: Raised during the failure of the issue viewing process.
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
