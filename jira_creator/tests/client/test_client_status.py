from unittest.mock import MagicMock

from jira.client import JiraClient


def test_set_status():
    client = JiraClient()
    client._request = MagicMock()

    # Simulating the side effects for multiple calls
    client._request.side_effect = [{"transitions": [{"name": "Done", "id": "2"}]}, {}]

    client.set_status("AAP-123", "Done")

    # Assert that the request was called twice
    assert client._request.call_count == 2
