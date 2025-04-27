#!/usr/bin/env python
"""
This file contains test cases for the set_status method in a client class.
The test_set_status_valid_transition function tests the method with a valid transition to 'In Progress' status.
It mocks the response for GET and POST requests and asserts that the _request method is called twice.

The test_set_status_invalid_transition function tests the method with an invalid transition to 'Done' status.
It uses pytest.raises to capture the exception and asserts that the _request method is called only once.

Functions:
- test_set_status_valid_transition(client): Set the status of a client to a valid transition.
- test_set_status_invalid_transition(client): Check if setting an invalid status transition raises an exception.

Arguments:
- client (object): An object representing the client whose status needs to be updated.
"""

import pytest
from exceptions.exceptions import SetStatusError


def test_set_status_valid_transition(client):
    """
    Set the status of a client to a valid transition.

    Arguments:
    - client (object): An object representing the client whose status needs to be updated.

    Side Effects:
    - Modifies the status of the client to a valid transition.
    """

    # Mock response for GET and POST requests
    transitions = {"transitions": [{"name": "In Progress", "id": "31"}]}
    client.request.return_value = transitions  # First call is GET, second is POST

    # Call the set_status method
    client.set_status("AAP-test_set_status_valid_transition", "In Progress")

    # Assert that _request was called twice (GET and POST)
    assert client.request.call_count == 2


def test_set_status_invalid_transition(client):
    """
    Check if setting an invalid status transition raises an exception.

    Arguments:
    - client: An object representing the client to interact with the API.

    Side Effects:
    - Modifies the behavior of the client object by mocking the response for GET and POST requests.
    """

    # Mock response for GET and POST requests
    transitions = {"transitions": [{"name": "In Progress", "id": "31"}]}
    client.request.return_value = transitions  # First call is GET, second is POST

    # Use pytest.raises to capture the exception
    with pytest.raises(SetStatusError, match="❌ Transition to status 'Done' not found"):  # fmt: skip
        client.set_status("AAP-test_set_status_invalid_transition", "Done")

    # Ensure _request was called twice (GET and POST)
    assert client.request.call_count == 1
