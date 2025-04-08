from unittest.mock import MagicMock

import pytest
from exceptions.exceptions import UnassignIssueError


def test_unassign_issue_fails(capsys, client):
    # Mock the _request method to simulate an exception
    client._request = MagicMock(side_effect=UnassignIssueError("fail"))

    with pytest.raises(UnassignIssueError):
        # Call unassign_issue and assert the result
        client.unassign_issue("AAP-test_unassign_issue_fails")

    # Check that the error message was captured in the output
    out = capsys.readouterr().out
    assert "❌ Failed to unassign issue" in out
