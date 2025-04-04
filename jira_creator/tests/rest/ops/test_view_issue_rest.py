from unittest.mock import MagicMock

from rest.client import JiraClient


def test_rest_view_issue():
    client = JiraClient()
    client._request = MagicMock()

    # Call the method to set priority
    client.view_issue("AAP-123")

    # Update the test to expect the 'allow_204' argument
    client._request.assert_called_once_with(
        "GET",
        "/rest/api/2/issue/AAP-123",
    )
