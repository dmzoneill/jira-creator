#!/usr/bin/env python
"""
This module contains unit tests for the 'blocked' function within the CLI class, focusing on various scenarios related
to blocked issues in a project management context.

The test cases include:
- `test_blocked_issues_found`: Verifies behavior when blocked issues are present.
- `test_blocked_no_issues`: Checks the response when no issues are found.
- `test_blocked_none_blocked`: Validates the output when issues are listed but none are blocked.
- `test_blocked_exception`: Tests the handling of exceptions raised during the listing of blocked issues.

Additionally, the module defines an `Args` class to encapsulate project-related arguments such as project name,
component, and user.
"""

from unittest.mock import MagicMock

import pytest
from core.env_fetcher import EnvFetcher
from exceptions.exceptions import ListBlockedError


class Args:
    """
    A class to store information about project arguments.

    Attributes:
    project (str): The name of the project.
    component (str): The component related to the project.
    user (str): The user associated with the project.
    """

    project = None
    component = None
    user = None


def test_blocked_issues_found(cli, capsys):
    """
    Set up a mock Jira instance for testing purposes.

    Arguments:
    - cli: Command Line Interface object.
    - capsys: Pytest fixture for capturing stdout and stderr.

    Side Effects:
    - Initializes a MagicMock Jira instance on the cli object for testing.
    """

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
    """
    Summary:
    Simulates a test scenario where no issues are blocked, using a provided CLI object and capsys for capturing system
    output.

    Arguments:
    - cli: An object representing the CLI (Command Line Interface) with a 'jira' attribute.
    - capsys: A pytest fixture for capturing stdout and stderr output during the test.

    Side Effects:
    - Modifies the 'jira' attribute of the provided 'cli' object by setting it to a MagicMock.
    - Configures the 'list_issues' method of the 'jira' attribute to return an empty list ([]).
    """

    cli.jira = MagicMock()
    cli.jira.list_issues.return_value = []

    cli.blocked(Args())

    out = capsys.readouterr().out
    assert "✅ No issues found." in out


def test_blocked_none_blocked(cli, capsys):
    """
    Check if there are any blocked issues in JIRA.

    Arguments:
    - cli: An object representing the command-line interface.
    - capsys: A fixture for capturing stdout and stderr output.

    Return: N/A
    """

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
    """
    Simulate a test scenario where a ListBlockedError exception is raised when calling the list_issues method on a Jira
    client object.

    Arguments:
    - cli: An object representing a Jira client.
    - capsys: A fixture for capturing stdout and stderr output during testing.

    Exceptions:
    - ListBlockedError: Raised when an issue is blocked, with an error message indicating the blockage.

    Side Effects:
    - Modifies the behavior of the list_issues method of the Jira client object to raise a ListBlockedError.

    Note: This function is typically used in testing to handle and test scenarios where specific exceptions are raised.
    """

    cli.jira = MagicMock()
    cli.jira.list_issues.side_effect = ListBlockedError("Boom!")

    with pytest.raises(ListBlockedError):
        cli.blocked(Args())

    out = capsys.readouterr().out
    assert "❌ Failed to list blocked issues" in out
