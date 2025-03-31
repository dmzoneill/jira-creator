from unittest.mock import MagicMock

from jira.ops.assign_issue import assign_issue


def test_assign_issue_success():
    mock_request = MagicMock()
    result = assign_issue(mock_request, "ABC-123", "johndoe")

    # Verify function returns True
    assert result is True

    args, kwargs = mock_request.call_args
    assert args == ("PUT", "/rest/api/2/issue/ABC-123")
    assert kwargs["json"] == {"fields": {"assignee": {"name": "johndoe"}}}


def test_assign_issue_failure(capfd):
    def fail_request(*args, **kwargs):
        raise Exception("kaboom")

    result = assign_issue(fail_request, "ABC-123", "johndoe")
    out, _ = capfd.readouterr()

    assert result is False
    assert "❌ Failed to assign issue ABC-123" in out
