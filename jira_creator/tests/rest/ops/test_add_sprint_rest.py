#!/usr/bin/env python
"""
This file contains unit tests for the 'add_to_sprint_by_name' method of a client class.
The tests cover scenarios where the sprint is successfully found and when it is not found.
Mock objects are used to simulate the behavior of the '_request' method for sprint lookup and assignment.
The tests assert the correct behavior of the method by checking the number of method calls and exception messages.

Functions:
- test_add_to_sprint_by_name_success(client): Add a sprint to the client by name successfully.
- test_add_to_sprint_by_name_not_found(client): Simulate a scenario where a sprint is not found by adding it to the
sprint by name.

Arguments:
- client: A client object used to interact with a service.

Side Effects:
- Modifies the client object by adding a sprint to it in the 'test_add_to_sprint_by_name_success' function.
- Modifies the _request method of the client object to return an empty list when called in the
'test_add_to_sprint_not_found' function.
"""

from unittest.mock import MagicMock

import pytest
from exceptions.exceptions import AddSprintError


def test_add_to_sprint_success(client):
    """
    Add a sprint to the client by name successfully.

    Arguments:
    - client: A client object used to interact with a service.

    Side Effects:
    - Modifies the client object by adding a sprint to it.
    """

    # Mock the _request method to simulate sprint lookup and assignment
    client.request = MagicMock(
        side_effect=[
            {"values": [{"id": 88, "name": "Sprint 42"}]},  # Sprint lookup
            {"name": "user1"},
            {},
            {},
        ]
    )

    # Call the add_to_sprint_by_name method
    client.add_to_sprint("AAP-test_add_to_sprint_by_name_success", "Sprint 42", "")

    # Assert that _request was called twice
    assert client.request.call_count == 4


def test_add_to_sprint_not_found(client):
    """
    Simulate a scenario where a sprint is not found by adding it to the sprint by name.

    Arguments:
    - client: An object representing the client used to interact with a service.

    Side Effects:
    - Modifies the _request method of the client object to return an empty list when called.
    """

    # Mock the _request method to simulate sprint lookup where the sprint is not found
    client.request = MagicMock(return_value={"values": []})

    # Try to add the issue to a non-existent sprint and check for the exception
    with pytest.raises(AddSprintError) as exc:
        client.add_to_sprint(
            "AAP-test_add_to_sprint_not_found", "Nonexistent Sprint", ""
        )

    # Assert that the exception message contains 'Could not find sprint'
    assert "Could not find sprint" in str(exc.value)
