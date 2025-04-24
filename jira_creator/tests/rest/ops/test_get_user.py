#!/usr/bin/env python
"""
This script contains a unit test function to test the 'get_user' method of a client class. It mocks a user data
dictionary and sets up a MagicMock object to simulate the behavior of the '_request' method of the client class. The
test verifies that the 'get_user' method returns the expected user data by comparing the result with the mock user data
dictionary. It also asserts that the '_request' method is called once with specific parameters.

Functions:
- test_get_user_returns_expected_data(client): Retrieve user data from the client using a mock user object.

Arguments:
- client (object): An object representing the client to interact with.

Side Effects:
- Modifies the client's _request method to return a mock user object.
"""

from unittest.mock import MagicMock


def test_get_user_returns_expected_data(client):
    """
    Retrieve user data from the client using a mock user object.

    Arguments:
    - client (object): An object representing the client to interact with.

    Side Effects:
    - Modifies the client's _request method to return a mock user object.
    """

    mock_user = {
        "name": "daoneill",
        "displayName": "David O'Neill",
        "emailAddress": "daoneill@redhat.com",
    }
    client.request = MagicMock(return_value=mock_user)

    result = client.get_user("daoneill")

    assert result == mock_user
    client.request.assert_called_once_with(
        "GET", "/rest/api/2/user", params={"username": "daoneill"}
    )
