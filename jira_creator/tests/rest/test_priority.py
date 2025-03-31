from unittest.mock import MagicMock

from jira.client import JiraClient


def test_set_priority():
    client = JiraClient()
    client._request = MagicMock()

    # Call the method to set priority
    client.set_priority("AAP-123", "High")

    # Update the test to expect the 'allow_204' argument
    client._request.assert_called_once_with(
        "PUT",
        "/rest/api/2/issue/AAP-123",
        json={"fields": {"priority": {"name": "High"}}},
    )
