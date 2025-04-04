from unittest.mock import MagicMock

import pytest
from rest.client import JiraClient


def test_set_status_valid_transition():
    client = JiraClient()

    # Mock the _request method
    client._request = MagicMock()

    # Mock response for GET and POST requests
    transitions = {"transitions": [{"name": "In Progress", "id": "31"}]}
    client._request.return_value = transitions  # First call is GET, second is POST

    # Call the set_status method
    client.set_status("AAP-1", "In Progress")

    # Assert that _request was called twice (GET and POST)
    assert client._request.call_count == 2


def test_set_status_invalid_transition():
    client = JiraClient()

    # Mock the _request method
    client._request = MagicMock()

    # Mock response for GET and POST requests
    transitions = {"transitions": [{"name": "In Progress", "id": "31"}]}
    client._request.return_value = transitions  # First call is GET, second is POST

    # Use pytest.raises to capture the exception
    with pytest.raises(Exception, match="❌ Transition to status 'Done' not found"):
        client.set_status("AAP-1", "Done")

    # Ensure _request was called twice (GET and POST)
    assert client._request.call_count == 1
