from unittest.mock import MagicMock

import pytest
from jira.client import JiraClient


def test_change_issue_type_fails():
    # Create an instance of JiraClient
    client = JiraClient()

    # Mock the _request method to raise an exception
    client._request = MagicMock(side_effect=Exception("failure"))

    # Attempt to change the issue type
    success = client.change_issue_type("AAP-1", "task")

    # Assert that the operation failed
    assert not success
