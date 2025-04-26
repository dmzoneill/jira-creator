#!/usr/bin/env python
"""
This file contains a unit test function to test the behavior of the set_status method in the client object.
The test checks for the scenario where a valid status transition is missing in the transitions list.
The _request method of the client object is mocked using MagicMock to simulate the absence of valid transitions.
An exception, SetStatusError, is expected to be raised when trying to set a specific status that is not found in the
transitions list.

The test_status_transition_missing function mocks the _request method of the client object using MagicMock.
It takes the client object as an argument and modifies the _request method to return an empty list of transitions.
The function tests the behavior of the client object when trying to set a status that does not have a valid transition.
It expects a SetStatusError to be raised when a valid transition to the specified status is not found.
"""
from unittest.mock import MagicMock

import pytest
from exceptions.exceptions import SetStatusError


def test_status_transition_missing(client):
    """
    Mock the _request method of the client object using MagicMock.

    Arguments:
    - client: An object representing the client for which the _request method is being mocked.

    Exceptions:
    - SetStatusError: Raised when a valid transition to the specified status is not found.

    Side Effects:
    - Modifies the _request method of the client object to return an empty list of transitions.

    The function tests the behavior of the client object when trying to set a status that does not have a valid
    transition.
    """

    # Mock the _request method
    client.request = MagicMock()

    # Simulate an empty list of transitions (no valid transition found)
    client.request.return_value = {"transitions": []}

    # Assert that an exception is raised when trying to set a status
    with pytest.raises(SetStatusError, match="Transition to status 'done' not found"):
        client.set_status("AAP-test_status_transition_missing", "done")
