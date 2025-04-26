#!/usr/bin/env python
"""
This script defines a unit test function test_search_users_returns_expected_data(client) that tests the search_users
method of a client object. The function sets up a mock response for the client's _request method and then calls the
search_users method with a specific username. It asserts that the results match the mock response and checks that the
_request method was called with the expected parameters. The script requires the client object to be passed as an
argument to the test function.

The test_search_users_returns_expected_data function:
- Searches for users and returns the expected data.
- Takes a client object as an argument representing the client used to make requests.
- Modifies the client's _request attribute to return mock user data.
"""

from unittest.mock import MagicMock


def test_search_users_returns_expected_data(client):
    """
    Search for users and return the expected data.

    Arguments:
    - client (Client): An object representing the client used to make requests.

    Side Effects:
    - Modifies the client's _request attribute to return mock user data.
    """

    mock_users = [
        {"name": "daoneill", "displayName": "David O'Neill"},
        {"name": "jdoe", "displayName": "John Doe"},
    ]
    client.request = MagicMock(return_value=mock_users)

    results = client.search_users("daoneill")

    assert results == mock_users
    client.request.assert_called_once_with(
        "GET",
        "/rest/api/2/user/search",
        params={"username": "daoneill", "maxResults": 10},
    )
