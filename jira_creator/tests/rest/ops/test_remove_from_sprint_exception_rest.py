#!/usr/bin/env python
"""
This script contains a unit test function to test the behavior of the remove_from_sprint method in a client class. It
mocks the _request method to raise a RemoveFromSprintError exception with a specified message. The test checks if the
exception is properly raised when calling the remove_from_sprint method with a specific parameter. It also captures the
output to verify that the expected error message is printed.

Functions:
- test_remove_from_sprint_error: Mocks the _request method to raise a RemoveFromSprintError exception when called with
the argument "fail". It takes capsys (a fixture provided by pytest to capture stdout and stderr output) and client (an
object representing a client used to make requests) as parameters.
"""

from unittest.mock import MagicMock

import pytest
from exceptions.exceptions import RemoveFromSprintError


def test_remove_from_sprint_error(capsys, client):
    """
    Mock the _request method to raise a RemoveFromSprintError exception when called with the argument "fail".

    :param capsys: A fixture provided by pytest to capture stdout and stderr output.
    :param client: An object representing a client used to make requests.
    """

    # Mock the _request method to raise an exception
    client.request = MagicMock(side_effect=RemoveFromSprintError("fail"))

    with pytest.raises(RemoveFromSprintError):
        # Call the remove_from_sprint method
        client.remove_from_sprint("AAP-test_remove_from_sprint_error")

    # Capture the output and assert the error message
    out = capsys.readouterr().out
    assert "❌ Failed to remove from sprint" in out
