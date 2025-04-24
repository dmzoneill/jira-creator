#!/usr/bin/env python
"""
This script defines a test case function to test the get_issue_type method of a client class. The client's _request
method is mocked using MagicMock to simulate a successful response. The get_issue_type method is called with a sample
issue key, and the result is asserted to be the expected issue type "Story". Additionally, it checks if the _request
method was called with the expected arguments.

The test_get_issue_type function simulates getting the type of an issue from a client. It takes an object representing
the client to interact with as an argument. The function modifies the client by mocking the _request method to return a
simulated successful response.
"""

from unittest.mock import MagicMock


def test_get_issue_type(client):
    """
    Simulate getting the type of an issue from a client.

    Arguments:
    - client: An object representing the client to interact with.

    Side Effects:
    - Modifies the client by mocking the _request method to return a simulated successful response.
    """

    # Mock the _request method to simulate a successful response
    client.request = MagicMock(
        return_value={"fields": {"issuetype": {"name": "Story"}}}
    )

    # Call the get_issue_type method with a sample issue key
    result = client.get_issue_type("AAP-test_get_issue_type")

    # Check if the result is the correct issue type
    assert result == "Story"
    # Ensure that _request was called with the expected arguments
    client.request.assert_called_once_with(
        "GET", "/rest/api/2/issue/AAP-test_get_issue_type"
    )
