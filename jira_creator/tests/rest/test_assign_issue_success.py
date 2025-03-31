from unittest.mock import MagicMock

from jira.client import JiraClient


def test_assign_issue_failure(capfd):
    client = JiraClient()

    # Simulate a failure by raising an exception
    def mock_request_fail(*args, **kwargs):
        raise Exception("kaboom")

    client._request = mock_request_fail

    result = client.assign_issue("AAP-100", {"name": "johndoe"})
    out = capfd.readouterr().out

    assert result is False
    assert "❌ Failed to assign issue AAP-100" in out
