#!/usr/bin/env python
"""
This file contains a unit test function to test the unassign_issue method of a client class. The test case simulates an
UnassignIssueError exception by mocking the _request method using MagicMock. The test asserts that calling
unassign_issue with a specific issue identifier raises the expected exception and captures the error message in the
output.

The test_unassign_issue_fails function mocks the _request method of a client object to simulate an UnassignIssueError
exception when called. It is used for testing purposes.

Arguments:
- capsys: A pytest fixture for capturing stdout and stderr output.
- client: An object representing a client, typically used for making requests.
"""

from unittest.mock import MagicMock

import pytest
from exceptions.exceptions import UnassignIssueError


def test_unassign_issue_fails(capsys, client):
    """
    Mocks the _request method of a client object to simulate an UnassignIssueError exception when called. Used for
    testing purposes.

    Arguments:
    - capsys: A pytest fixture for capturing stdout and stderr output.
    - client: An object representing a client, typically used for making requests.

    """

    # Mock the _request method to simulate an exception
    client.request = MagicMock(side_effect=UnassignIssueError("fail"))

    with pytest.raises(UnassignIssueError):
        # Call unassign_issue and assert the result
        client.unassign_issue("AAP-test_unassign_issue_fails")

    # Check that the error message was captured in the output
    out = capsys.readouterr().out
    assert "❌ Failed to unassign issue" in out
