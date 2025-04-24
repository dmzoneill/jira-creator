#!/usr/bin/env python
"""
Simulate unassigning an issue from a client.

Arguments:
- client: An object representing a client. It is used to interact with the client's system.

Side Effects:
- Modifies the client object by mocking the _request method to simulate a successful request.
"""
from unittest.mock import MagicMock


def test_unassign_issue(client):
    """
    Simulate unassigning an issue from a client.

    Arguments:
    - client: An object representing a client. It is used to interact with the client's system.

    Side Effects:
    - Modifies the client object by mocking the _request method to simulate a successful request.
    """

    # Mock the _request method to simulate a successful request
    client.request = MagicMock(return_value={})

    # Call unassign_issue and assert the result
    result = client.unassign_issue("AAP-test_unassign_issue")
    assert result is True
