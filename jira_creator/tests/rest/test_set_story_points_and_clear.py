from unittest.mock import MagicMock

from jira.client import JiraClient


def test_set_story_points():
    client = JiraClient()
    client._request = MagicMock(return_value={})

    # Call the function to set story points
    client.set_story_points("AAP-123", 8)

    # Assert that the PUT request is called with the correct payload and endpoint
    client._request.assert_called_once_with(
        "PUT",
        "/rest/api/2/issue/AAP-123",
        json={"fields": {"customfield_12310243": 8}},
    )
