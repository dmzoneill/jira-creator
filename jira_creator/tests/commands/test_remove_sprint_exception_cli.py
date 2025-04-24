#!/usr/bin/env python
"""
This file contains a unit test for the remove_sprint method. It mocks the remove_from_sprint method to raise a
RemoveFromSprintError exception and tests the behavior of the remove_sprint method when this exception is raised. The
test asserts that the error message "❌ Failed to remove sprint" is displayed when the exception occurs.

Functions:
- test_remove_sprint_error: Mocks the remove_from_sprint method to raise an exception during testing. It takes two
arguments:
- cli (object): The CLI object used for testing.
- capsys (object): The pytest built-in fixture capsys for capturing stdout and stderr.

Exceptions:
- RemoveFromSprintError: An exception raised when attempting to remove an issue from a sprint.
"""

from unittest.mock import MagicMock

import pytest
from exceptions.exceptions import RemoveFromSprintError


def test_remove_sprint_error(cli, capsys):
    """
    Mock the remove_from_sprint method to raise an exception during testing.

    Arguments:
    - cli (object): The CLI object used for testing.
    - capsys (object): The pytest built-in fixture capsys for capturing stdout and stderr.

    Exceptions:
    - RemoveFromSprintError: An exception raised when attempting to remove an issue from a sprint.
    """

    # Mock the remove_from_sprint method to raise an exception
    cli.jira.remove_from_sprint = MagicMock(side_effect=RemoveFromSprintError("fail"))

    class Args:
        issue_key = "AAP-test_remove_sprint_error"

    with pytest.raises(RemoveFromSprintError):
        # Call the remove_sprint method
        cli.remove_sprint(Args())

    # Capture the output and assert the error message
    out = capsys.readouterr().out
    assert "❌ Failed to remove sprint" in out
