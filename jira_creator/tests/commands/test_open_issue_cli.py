#!/usr/bin/env python
"""
This module contains unit tests for the 'open_issue' method in the CLI class.
The tests include scenarios for successful execution and exception handling.
The 'test_open_issue' function simulates the successful opening of an issue by patching subprocess.Popen.
It asserts that the correct arguments are passed to subprocess.Popen.
The 'test_open_issue_exception_handling' function simulates an exception during issue opening.
It asserts that the exception is properly handled and the error message is printed.
"""

from unittest.mock import patch

import pytest
from exceptions.exceptions import OpenIssueError


def test_open_issue(cli):
    """
    Prevents opening a process by patching subprocess.Popen.

    Arguments:
    - cli (str): The command line interface command to be executed.

    Side Effects:
    - Modifies the behavior of subprocess.Popen to prevent opening a process.
    """

    # Patch subprocess.Popen to prevent actually opening a process
    with patch("subprocess.Popen") as mock_popen:

        class Args:
            issue_key = "AAP-test_open_issue"

        # Simulate subprocess.Popen succeeding
        mock_popen.return_value = True

        # Call the method
        cli.open_issue(Args())

        # Assert that subprocess.Popen was called with the correct arguments
        mock_popen.assert_called_once_with(
            ["xdg-open", "https://example.atlassian.net/browse/AAP-test_open_issue"]
        )


def test_open_issue_exception_handling(cli):
    """
    Simulates exception handling when opening an issue using a CLI tool.

    Arguments:
    - cli (str): The command-line interface (CLI) tool used to open the issue.

    Exceptions:
    - OpenIssueError: Raised when there is a failure to open the issue using the CLI tool.
    """

    # Patch subprocess.Popen to simulate an exception
    with patch("subprocess.Popen") as mock_popen:

        class Args:
            issue_key = "AAP-test_open_issue_exception_handling"

        # Simulate subprocess.Popen raising an exception
        mock_popen.side_effect = OpenIssueError("Failed to open issue")

        # Call the method
        with patch("builtins.print") as mock_print:  # Mock print to check the output
            with pytest.raises(OpenIssueError):
                cli.open_issue(Args())

            # Assert that print was called with the correct error message
            mock_print.assert_called_once_with(
                "❌ Failed to open issue AAP-test_open_issue_exception_handling: Failed to open issue"
            )
