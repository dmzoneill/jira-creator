from unittest.mock import MagicMock

import pytest
from exceptions.exceptions import AssignIssueError
from rest.ops.assign_issue import assign_issue


def test_assign_issue_success():
    mock_request = MagicMock()
    result = assign_issue(mock_request, "ABC-123", "johndoe")

    # Verify function returns True
    assert result is True

    args, kwargs = mock_request.call_args
    assert args == ("PUT", "/rest/api/2/issue/ABC-123")
    assert kwargs["json"] == {"fields": {"assignee": {"name": "johndoe"}}}


def test_assign_issue_failure(capsys, client):
    client._request = MagicMock(side_effect=AssignIssueError("fail"))

    with pytest.raises(AssignIssueError):
        client.assign_issue("ABC-123", "johndoe")

    capsys, _ = capsys.readouterr()
    assert "❌ Failed to assign issue ABC-123" in capsys
