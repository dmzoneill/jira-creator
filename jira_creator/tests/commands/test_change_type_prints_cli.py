#!/usr/bin/env python
"""
This file contains a unit test for the 'change_type' method in the 'cli' module. The test verifies that the method
correctly changes the issue type in Jira and prints the expected output message. It mocks the 'change_issue_type'
method using a MagicMock object and captures the output using capsys. The test case asserts that the printed output
matches the expected message indicating a successful change of issue type.

The 'test_change_type_prints' function simulates changing the type of an issue and prints the result. It takes two
arguments:
- cli: Command-line interface object for interacting with Jira.
- capsys: Pytest fixture for capturing stdout and stderr.

Side Effects:
- Mocks the change_issue_type method to return True.
"""

from unittest.mock import MagicMock


def test_change_type_prints(cli, capsys):
    """
    Simulate changing the type of an issue and print the result.

    Arguments:
    - cli: Command-line interface object for interacting with Jira.
    - capsys: Pytest fixture for capturing stdout and stderr.

    Side Effects:
    - Mocks the change_issue_type method to return True.
    """

    # Mocking the change_issue_type method
    cli.jira.change_issue_type = MagicMock(return_value=True)

    class Args:
        issue_key = "AAP-test_change_type_prints"
        new_type = "story"

    # Call the method
    cli.change_type(Args())

    # Capture the output
    out = capsys.readouterr().out
    # Correct the expected output to match the actual printed output
    assert "✅ Changed AAP-test_change_type_prints to 'story'" in out
