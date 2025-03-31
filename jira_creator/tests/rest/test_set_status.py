from unittest.mock import MagicMock

import pytest
from jira.client import JiraClient


def test_set_status_transitions():
    client = JiraClient()

    # Mock the _request method
    client._request = MagicMock()

    # Mock response for GET and POST requests
    transitions = {"transitions": [{"name": "In Progress", "id": "31"}]}
    client._request.side_effect = [transitions, {}]  # First call is GET, second is POST

    # Call the set_status method
    client.set_status("AAP-1", "In Progress")

    # Assert that _request was called twice (GET and POST)
    assert client._request.call_count == 2
