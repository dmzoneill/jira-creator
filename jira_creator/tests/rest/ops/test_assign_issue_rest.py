#!/usr/bin/env python
"""
This script contains unit tests for the 'assign_issue' function in the 'rest.ops.assign_issue' module.
The tests cover both success and failure scenarios of the function.

Functions:
- test_assign_issue_success(): Assign an issue to a user.
Arguments:
- mock_request (MagicMock): A MagicMock object representing the request.
- issue_key (str): The key of the issue to be assigned.
- assignee (str): The username of the user to whom the issue will be assigned.

- test_assign_issue_failure(capsys, client): Assign a failure issue to the client for testing purposes.
Arguments:
- capsys (pytest fixture): Pytest fixture for capturing stdout and stderr.
- client: An instance of a client object.

Side Effects:
- Modifies the client's _request attribute by setting it to a MagicMock object with a side effect of raising an
AssignIssueError with message "fail".
"""

from unittest.mock import MagicMock

import pytest
from exceptions.exceptions import AssignIssueError
from rest.ops.assign_issue import assign_issue


def test_assign_issue_success():
    """
    Assign an issue to a user.

    Arguments:
    - mock_request (MagicMock): A MagicMock object representing the request.
    - issue_key (str): The key of the issue to be assigned.
    - assignee (str): The username of the user to whom the issue will be assigned.
    """

    mock_request = MagicMock()
    result = assign_issue(mock_request, "ABC-123", "johndoe")

    # Verify function returns True
    assert result is True

    args, kwargs = mock_request.call_args
    assert args == ("PUT", "/rest/api/2/issue/ABC-123")
    assert kwargs["json_data"] == {"fields": {"assignee": {"name": "johndoe"}}}


def test_assign_issue_failure(capsys, client):
    """
    Assign a failure issue to the client for testing purposes.

    Arguments:
    - capsys (pytest fixture): Pytest fixture for capturing stdout and stderr.
    - client: An instance of a client object.

    Side Effects:
    - Modifies the client's _request attribute by setting it to a MagicMock object with a side effect of raising an
    AssignIssueError with message "fail".
    """

    client.request = MagicMock(side_effect=AssignIssueError("fail"))

    with pytest.raises(AssignIssueError):
        client.assign_issue("ABC-123", "johndoe")

    capsys, _ = capsys.readouterr()
    assert "❌ Failed to assign issue ABC-123" in capsys
