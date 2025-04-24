#!/usr/bin/env python
"""
This file contains unit tests for the list_sprints method in a CLI application.
The tests use the pytest framework along with unittest.mock to mock the behavior of the list_sprints method.
The test_list_sprints function tests the successful execution of list_sprints, while the test_list_sprints_exception
function tests the exception handling when list_sprints raises an exception.
Both tests mock the list_sprints method and capture the output using capsys to perform assertions on the expected
output.

test_list_sprints:
- Mocks the list_sprints method of the Jira CLI object to return a list of sprints ["Sprint 1", "Sprint 2"] for testing.
- Arguments:
- cli: The CLI object used to interact with Jira.
- capsys: The built-in pytest fixture for capturing stdout and stderr.

test_list_sprints_exception:
- Mocks the list_sprints method to raise an exception when called.
- Args:
- cli: An object representing the CLI.
- capsys: A fixture provided by pytest to capture stdout and stderr.
- Exceptions:
- Exception: Raised when the list_sprints method is called to simulate a failure.
"""

from unittest.mock import MagicMock

import pytest


def test_list_sprints(cli, capsys):
    """
    Mock the list_sprints method for testing purposes.

    Arguments:
    - cli: The CLI object used to interact with Jira.
    - capsys: The built-in pytest fixture for capturing stdout and stderr.

    Side Effects:
    - Mocks the list_sprints method of the Jira CLI object to return a list of sprints ["Sprint 1", "Sprint 2"] for
    testing.
    """

    # Mock the list_sprints method
    response = MagicMock()
    cli.jira.list_sprints = MagicMock(return_value=["Sprint 1", "Sprint 2"])

    class Args:
        board_id = "dummy_issue_key"  # Not used in the method

    response = cli.list_sprints(Args())

    # Capture output and assert
    out = capsys.readouterr().out
    assert "Sprint 1" in out
    assert "Sprint 2" in out
    assert response == ["Sprint 1", "Sprint 2"]


def test_list_sprints_exception(cli, capsys):
    """
    Mock the list_sprints method to raise an exception when called.

    Args:
    cli: An object representing the CLI.
    capsys: A fixture provided by pytest to capture stdout and stderr.

    Exceptions:
    Exception: Raised when the list_sprints method is called to simulate a failure.
    """

    # Mock the list_sprints method
    cli.jira.list_sprints = MagicMock(side_effect=Exception("Failed"))

    class Args:
        board_id = "dummy_issue_key"  # Not used in the method

    with pytest.raises(Exception):
        cli.list_sprints(Args())
