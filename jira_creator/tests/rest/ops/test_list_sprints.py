#!/usr/bin/env python
"""
Test the functionality of listing sprints for a given board using a client object.

Parameters:
- client: An object representing the client to interact with the board.
"""

from unittest.mock import MagicMock


def test_list_sprints(client):
    """
    Retrieves a list of open sprints from a specified board using the provided client.

    Arguments:
    - client: An object representing the client used to make requests.

    No return value.

    Side Effects:
    - Modifies the client's '_request' attribute to a MagicMock object.
    """

    values = {
        "values": [
            {"name": "Sprint 1", "state": "open"},
            {"name": "Sprint 2", "state": "open"},
        ]
    }
    request_mock = MagicMock(return_value=values)
    client.request = request_mock
    board_id = "dummy_board_id"

    response = client.list_sprints(board_id)

    assert response == ["Sprint 1", "Sprint 2"]
