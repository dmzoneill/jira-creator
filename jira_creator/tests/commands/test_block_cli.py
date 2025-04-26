#!/usr/bin/env python
"""
This module contains test cases for the 'block' command functionality in a command-line interface (CLI) application.
It includes two main test functions: `test_block_command`, which verifies the successful blocking of an issue, and
`test_block_command_exception`, which checks the handling of a `BlockError` exception during the blocking process.
The tests leverage pytest fixtures `cli` and `capsys` to simulate the CLI environment and capture output, respectively.
Mock implementations of the issue blocking mechanism are used to ensure isolation from actual system behavior during
testing.
"""

import pytest
from exceptions.exceptions import BlockError


def test_block_command(cli, capsys):
    """
    Execute a test for a block command function.

    Arguments:
    - cli: An object representing the command-line interface for testing purposes.
    - capsys: A fixture provided by pytest for capturing stdout and stderr outputs during testing.

    Side Effects:
    - Initializes an empty dictionary called 'called' to keep track of function calls.
    """

    called = {}

    def mock_block_issue(issue_key, reason):
        """
        Sets the provided issue key and reason in a dictionary.

        Arguments:
        - issue_key (str): The key of the issue to be mocked.
        - reason (str): The reason for mocking the issue.

        Side Effects:
        - Modifies the global dictionary 'called' by setting 'issue_key' and 'reason' keys with the provided values.
        """

        called["issue_key"] = issue_key
        called["reason"] = reason

    cli.jira.block_issue = mock_block_issue

    class Args:
        issue_key = "AAP-test_block_command"
        reason = "Blocked by external dependency"

    cli.block(Args())

    captured = capsys.readouterr()
    assert "✅ AAP-test_block_command marked as blocked" in captured.out
    assert called == {
        "issue_key": "AAP-test_block_command",
        "reason": "Blocked by external dependency",
    }


def test_block_command_exception(cli, capsys):
    """
    Execute a test for a block command exception.

    Arguments:
    - cli (object): An instance of the command-line interface to test.
    - capsys (object): Pytest fixture to capture stdout and stderr outputs.

    Side Effects:
    - Executes a test for a block command exception in the provided command-line interface.
    """

    def mock_block_issue(issue_key, reason):
        """
        Simulates blocking an issue in a system.

        Arguments:
        - issue_key (str): The key or identifier of the issue to be blocked.
        - reason (str): The reason for blocking the issue.

        Exceptions:
        - BlockError: Raised when the function fails to block the issue (simulated failure).
        """

        raise BlockError("Simulated failure")

    cli.jira.block_issue = mock_block_issue

    class Args:
        issue_key = "AAP-test_block_command_exception"
        reason = "Something went wrong"

    with pytest.raises(BlockError):
        cli.block(Args())

    captured = capsys.readouterr()
    assert (
        "❌ Failed to mark AAP-test_block_command_exception as blocked: Simulated failure"
        in captured.out
    )
