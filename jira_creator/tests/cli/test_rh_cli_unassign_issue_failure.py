from unittest.mock import MagicMock

from jira.client import JiraClient


def test_unassign_issue_fails(capsys):
    client = JiraClient()

    # Mock the _request method to simulate an exception
    client._request = MagicMock(side_effect=Exception("fail"))

    # Call unassign_issue and assert the result
    result = client.unassign_issue("AAP-999")
    assert not result

    # Check that the error message was captured in the output
    out = capsys.readouterr().out
    assert "❌ Failed to unassign issue" in out
