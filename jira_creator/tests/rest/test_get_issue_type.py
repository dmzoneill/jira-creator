from unittest.mock import MagicMock

import pytest
from jira.client import JiraClient


def test_get_issue_type():
    # Create an instance of JiraClient
    client = JiraClient()

    # Mock the _request method to simulate a successful response
    client._request = MagicMock(
        return_value={"fields": {"issuetype": {"name": "Story"}}}
    )

    # Call the get_issue_type method with a sample issue key
    result = client.get_issue_type("AAP-123")

    # Check if the result is the correct issue type
    assert result == "Story"
    # Ensure that _request was called with the expected arguments
    client._request.assert_called_once_with("GET", "/rest/api/2/issue/AAP-123")
