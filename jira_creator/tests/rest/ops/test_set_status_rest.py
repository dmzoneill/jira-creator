import pytest


def test_set_status_valid_transition(client):
    # Mock response for GET and POST requests
    transitions = {"transitions": [{"name": "In Progress", "id": "31"}]}
    client._request.return_value = transitions  # First call is GET, second is POST

    # Call the set_status method
    client.set_status("AAP-test_set_status_valid_transition", "In Progress")

    # Assert that _request was called twice (GET and POST)
    assert client._request.call_count == 2


def test_set_status_invalid_transition(client):
    # Mock response for GET and POST requests
    transitions = {"transitions": [{"name": "In Progress", "id": "31"}]}
    client._request.return_value = transitions  # First call is GET, second is POST

    # Use pytest.raises to capture the exception
    with pytest.raises(Exception, match="❌ Transition to status 'Done' not found"):
        client.set_status("AAP-test_set_status_invalid_transition", "Done")

    # Ensure _request was called twice (GET and POST)
    assert client._request.call_count == 1
