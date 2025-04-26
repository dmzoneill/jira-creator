#!/usr/bin/env python
"""
Test function to verify the behavior of adding a sprint to a board with a specified name.

This function sets the board_id attribute of the client to None for testing purposes and then checks if an
AddSprintError exception is raised when the board_id is not set. It utilizes pytest for testing.

Arguments:
- client: An object representing a client with a board_id attribute.

This function does not return any value.
"""
import pytest
from exceptions.exceptions import AddSprintError


def test_add_to_sprint_board_id_check(client):
    """
    Set the board_id attribute of the client to None for testing purposes.

    Arguments:
    - client: An object representing a client with a board_id attribute.

    This function does not return any value.

    Exceptions:
    - AddSprintError: Raised when the board_id is not set in the environment.
    """

    # Mock the board_id attribute as None
    client.board_id = None

    # Check if the exception is raised when board_id is not set
    with pytest.raises(AddSprintError, match="JIRA_BOARD_ID not set in environment"):
        client.add_to_sprint(
            "AAP-test_add_to_sprint_board_id_check", "Sprint Alpha", ""
        )
