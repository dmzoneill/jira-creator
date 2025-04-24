#!/usr/bin/env python
"""
Get the current user from the client.

Arguments:
- client: An object representing the client to interact with. It is expected to have a '_request' method.

This function does not have a return value.
"""
from unittest.mock import MagicMock


def test_get_current_user(client):
    """
    Get the current user from the client.

    Arguments:
    - client: An object representing the client to interact with. It is expected to have a '_request' method.

    This function does not have a return value.
    """

    client.request = MagicMock(return_value={"name": "user123"})

    assert client.get_current_user() == "user123"
