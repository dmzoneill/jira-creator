#!/usr/bin/env python
"""
This file contains a test case for the 'change_issue_type' method of a client class.
It mocks the '_request' method to raise a 'ChangeIssueTypeError' exception and tests if the method correctly handles
the exception.
The test asserts that the expected error message is printed when the exception is raised.

Functions:
- test_change_issue_type_fails: Mocks the _request method to raise an exception when attempting to change the issue
type.
Args:
client (object): An object representing the client used to interact with the system.
capsys (object): An object used to capture stdout and stderr.
Exceptions:
ChangeIssueTypeError: Raised when the _request method encounters an issue while attempting to change the issue type.
"""

from unittest.mock import MagicMock

import pytest
from exceptions.exceptions import ChangeIssueTypeError


def test_change_issue_type_fails(client, capsys):
    """
    Mock the _request method to raise an exception when attempting to change the issue type.

    Args:
    client (object): An object representing the client used to interact with the system.
    capsys (object): An object used to capture stdout and stderr.

    Exceptions:
    ChangeIssueTypeError: Raised when the _request method encounters an issue while attempting to change the issue type.
    """

    # Mock the _request method to raise an exception
    client.request = MagicMock(side_effect=ChangeIssueTypeError("failure"))

    with pytest.raises(ChangeIssueTypeError):
        # Attempt to change the issue type
        client.change_issue_type("AAP-test_change_issue_type_fails", "task")

    # Capture the output
    out = capsys.readouterr().out

    # Assert that the correct output was printed
    assert "❌ Failed to change issue type:" in out
