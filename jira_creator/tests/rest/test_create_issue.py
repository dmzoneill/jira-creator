from unittest.mock import MagicMock

from jira.client import JiraClient


def test_create_issue():
    client = JiraClient()

    # Mock the _request method to return a response with a 'key'
    client._request = MagicMock(return_value={"key": "AAP-1"})

    # Call create_issue and assert that the returned key matches the mocked value
    key = client.create_issue({"fields": {"summary": "Test"}})
    assert key == "AAP-1"
