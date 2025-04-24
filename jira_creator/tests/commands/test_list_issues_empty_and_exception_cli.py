#!/usr/bin/env python
"""
This file contains unit tests for the 'list_issues' method in the 'cli' module.
It includes tests for the scenarios where the list of issues is empty and when an exception is raised.
Mocking of the 'list_issues' method is done using MagicMock to control its behavior during testing.
The tests verify the expected output messages when listing issues fails or when no issues are found.

Functions:
- test_list_issues_empty(cli, capsys): Mocks the list_issues method of a Jira CLI object to return an empty list for
testing purposes.
- test_list_issues_fail(cli, capsys): Simulates a failure scenario for listing issues in Jira.

Arguments:
- cli: A Jira CLI object.
- capsys: Pytest fixture to capture stdout and stderr output.

Exceptions:
- ListIssuesError: Raised when an error occurs while listing Jira issues.

Side Effects:
- Modifies the behavior of the list_issues method of the provided Jira CLI object.
- Modifies the behavior of the 'list_issues' method in the Jira command line interface to raise a 'ListIssuesError'
with message "fail".
"""

from unittest.mock import MagicMock

import pytest
from exceptions.exceptions import ListIssuesError


def test_list_issues_empty(cli, capsys):
    """
    Mock the list_issues method of a Jira CLI object to return an empty list for testing purposes.

    Args:
    cli: A Jira CLI object.
    capsys: Pytest fixture to capture stdout and stderr output.

    Side Effects:
    Modifies the behavior of the list_issues method of the provided Jira CLI object.
    """

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
    """
    Simulates a failure scenario for listing issues in Jira.

    Arguments:
    - cli: Jira command line interface object.
    - capsys: Pytest fixture for capturing stdout and stderr.

    Exceptions:
    - ListIssuesError: Raised when an error occurs while listing Jira issues.

    Side Effects:
    - Modifies the behavior of the 'list_issues' method in the Jira command line interface to raise a 'ListIssuesError'
    with message "fail".
    """

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
