#!/usr/bin/env python
"""
This file contains unit tests for the 'unblock' command of a CLI tool.
It includes two test functions:
- test_unblock_command_success: tests the successful execution of the 'unblock' command.
- test_unblock_command_failure: tests the failure scenario of the 'unblock' command when an UnBlockError is raised.

The tests use MagicMock and pytest to mock and assert the behavior of the CLI tool when unblocking an issue.
"""

from unittest.mock import MagicMock

import pytest
from exceptions.exceptions import UnBlockError


def test_unblock_command_success(cli, capsys):
    """
    Simulate a successful unblock command test.

    Arguments:
    - cli: The command-line interface object for testing.
    - capsys: Pytest fixture to capture stdout and stderr.

    Side Effects:
    - Initializes a dictionary called 'called' to keep track of function calls.
    """

    called = {}

    def mock_unblock(issue_key):
        """
        Summary:
        Updates a dictionary called `called` with the provided `issue_key`.

        Arguments:
        - issue_key (str): The key of the issue to be updated in the `called` dictionary.

        Side Effects:
        Modifies the `called` dictionary by adding or updating the key specified by `issue_key`.
        """

        called["issue_key"] = issue_key

    cli.jira.unblock_issue = mock_unblock

    class Args:
        issue_key = "AAP-test_unblock_command_success"

    cli.unblock(Args())

    out = capsys.readouterr().out
    assert "✅ AAP-test_unblock_command_success marked as unblocked" in out
    assert called["issue_key"] == "AAP-test_unblock_command_success"


def test_unblock_command_failure(cli, capsys):
    """
    Execute a test to validate the failure scenario of an unblock command.

    Arguments:
    - cli (object): An instance of the command line interface (CLI) to interact with the application.
    - capsys (object): A fixture to capture stdout and stderr outputs during the test.

    Side Effects:
    - Executes the unblock command in the CLI to trigger a failure scenario for testing purposes.
    """

    def raise_exception(issue_key):
        """
        Simulate an unblock failure by raising a custom UnBlockError exception.

        Arguments:
        - issue_key (str): A key representing the issue causing the unblock failure.

        Exceptions:
        - UnBlockError: Raised to simulate an unblock failure.
        """

        raise UnBlockError("Simulated unblock failure")

    cli.jira = MagicMock()
    cli.jira.unblock_issue = raise_exception

    class Args:
        issue_key = "AAP-test_unblock_command_failure"

    with pytest.raises(UnBlockError):
        cli.unblock(Args())

    out = capsys.readouterr().out
    assert "Simulated unblock failure" in out
