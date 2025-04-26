#!/usr/bin/env python
"""
Set the '_request' attribute of the client to a MagicMock object returning an empty dictionary.

This script contains a function 'test_remove_flag' that sets the '_request' attribute of the client object to a
MagicMock object returning an empty dictionary. It then calls the 'remove_flag' method on the client object and asserts
that the 'request' method was called with specific arguments.

Arguments:
- client: An object representing a client used to make requests.

Side Effects:
- Modifies the '_request' attribute of the client object.
"""
from unittest.mock import MagicMock


def test_remove_flag(client):
    """
    Set the '_request' attribute of the client to a MagicMock object returning an empty dictionary.

    Arguments:
    - client: An object representing a client used to make requests.

    Side Effects:
    - Modifies the '_request' attribute of the client object.
    """

    client.request = MagicMock(return_value={})

    client.remove_flag("AAP-test_remove_flag")

    client.request.assert_called_once_with(
        "POST",
        "/rest/greenhopper/1.0/xboard/issue/flag/flag.json",
        json_data={"issueKeys": ["AAP-test_remove_flag"]},
    )
