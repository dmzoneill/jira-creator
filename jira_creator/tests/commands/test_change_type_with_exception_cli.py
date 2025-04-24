#!/usr/bin/env python
"""
This file contains a test case function to test the failure scenario of changing the issue type. It mocks the
change_issue_type method to raise a ChangeTypeError exception and asserts that the proper error message is displayed.
The test case utilizes the pytest framework for testing and the MagicMock class for mocking the method.

test_change_type_failure(cli, capsys):
Mock the change_issue_type method to raise an exception for testing purposes.

Arguments:
- cli: An object representing the CLI interface.
- capsys: An object capturing stdout and stderr outputs during testing.

Exceptions:
- ChangeTypeError: Raised when the change_issue_type method encounters an error.
"""

from unittest.mock import MagicMock

import pytest
from exceptions.exceptions import ChangeTypeError


def test_change_type_failure(cli, capsys):
    """
    Mock the change_issue_type method to raise an exception for testing purposes.

    Arguments:
    - cli: An object representing the CLI interface.
    - capsys: An object capturing stdout and stderr outputs during testing.

    Exceptions:
    - ChangeTypeError: Raised when the change_issue_type method encounters an error.
    """

    # Mocking the change_issue_type method to raise an exception
    cli.jira.change_issue_type = MagicMock(side_effect=ChangeTypeError("Boom"))

    class Args:
        issue_key = "AAP-test_change_type_failure"
        new_type = "task"

    with pytest.raises(ChangeTypeError):
        # Call the method
        cli.change_type(Args())

    # Capture the output
    out = capsys.readouterr().out
    assert "❌ Error" in out
    assert "Boom" in out  # Optionally check that the exception message is included
