from unittest.mock import MagicMock

from jira.client import JiraClient


def test_unassign_issue():
    client = JiraClient()

    # Mock the _request method to simulate a successful request
    client._request = MagicMock(return_value={})

    # Call unassign_issue and assert the result
    result = client.unassign_issue("AAP-100")
    assert result is True
