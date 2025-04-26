#!/usr/bin/env python
"""
This script contains unit tests for the 'get_description' and 'update_description' methods of a client class.
It uses the unittest.mock library to simulate responses from the client's _request method.
The test_get_update_description function tests the functionality of retrieving and updating descriptions.
It asserts that the correct description is returned by get_description and that the description field is updated by
update_description.

test_get_update_description(client):
Retrieves the description field from a client using a mocked request.

Arguments:
- client: An object representing a client for which the description field needs to be retrieved.

This function mocks the _request method of the client object to simulate retrieving the description field.
No return value.
"""

from unittest.mock import MagicMock


def test_get_update_description(client):
    """
    Retrieves the description field from a client using a mocked request.

    Arguments:
    - client: An object representing a client for which the description field needs to be retrieved.

    This function mocks the _request method of the client object to simulate retrieving the description field.
    No return value.
    """

    # Mock _request method to simulate getting description
    client.request = MagicMock(return_value={"fields": {"description": "text"}})

    # Call get_description and assert it returns the correct description
    desc = client.get_description("AAP-test_get_update_description")
    assert desc == "text"

    # Create a dictionary to capture the updated fields
    updated = {}

    # Mock _request method to simulate updating description
    client.request = MagicMock(
        side_effect=lambda *a, **k: updated.update(k.get("json_data", {}))
    )

    # Call update_description and assert that the description field is updated
    client.update_description("AAP-test_get_update_description", "new text")
    assert "description" in updated["fields"]
