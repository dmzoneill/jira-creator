#!/usr/bin/env python
"""
This script contains a unit test function test_add_sprint_exception to test the handling of an exception in the
add_sprint method of a CLI application. The test mocks the add_to_sprint_by_name method using MagicMock to raise an
AddSprintError exception. It then calls the add_sprint method with specific arguments and asserts that the exception is
raised. The output is captured, and the presence of an expected failure message is checked. The test is designed to
verify the behavior of handling exceptions in the add_sprint method.

test_add_sprint_exception:
Mock the add_to_sprint_by_name method to raise an exception.

Arguments:
- cli: An object representing the command-line interface.
- capsys: A fixture provided by pytest to capture stdout and stderr.

Exceptions:
- AddSprintError: Raised when the add_to_sprint_by_name method encounters an error.
"""

from unittest.mock import MagicMock

import pytest
from exceptions.exceptions import AddSprintError


def test_add_sprint_exception(cli, capsys):
    """
    Mock the add_to_sprint_by_name method to raise an exception.

    Arguments:
    - cli: An object representing the command-line interface.
    - capsys: A fixture provided by pytest to capture stdout and stderr.

    Exceptions:
    - AddSprintError: Raised when the add_to_sprint_by_name method encounters an error.
    """

    # Mock the add_to_sprint_by_name method to raise an exception
    cli.jira.add_to_sprint = MagicMock(side_effect=AddSprintError("fail"))

    class Args:
        issue_key = "AAP-test_add_sprint_exception"
        sprint_name = "Sprint X"
        assignee = "user1"

    with pytest.raises(AddSprintError):
        # Call the add_sprint method and handle the exception
        cli.add_to_sprint(Args())

    # Capture the output
    out = capsys.readouterr().out

    # Check that the expected failure message is present
    assert "❌" in out
