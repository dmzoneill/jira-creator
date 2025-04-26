#!/usr/bin/env python
"""
Defines a unit test function to test the 'add_comment' method of a client object.

This function sets the return value of the '_request' method of the client to an empty dictionary when called. It then
calls the 'add_comment' method of the client with specific parameters and asserts that the '_request' method is called
with the expected arguments.

Arguments:
- client: An instance of a client object to be tested.

Side Effects:
- Modifies the return value of the '_request' method of the client to an empty dictionary.
"""
from unittest.mock import MagicMock


def test_add_comment(client):
    """
    Sets the return value of the _request method of the client to an empty dictionary when called.

    Arguments:
    - client: An instance of a client object.

    Side Effects:
    - Modifies the return value of the _request method of the client to an empty dictionary.
    """

    client.request = MagicMock(return_value={})

    client.add_comment("AAP-test_add_comment", "This is a comment")

    client.request.assert_called_once_with(
        "POST",
        "/rest/api/2/issue/AAP-test_add_comment/comment",
        json_data={"body": "This is a comment"},
    )
