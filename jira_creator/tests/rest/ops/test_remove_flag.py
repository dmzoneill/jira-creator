#!/usr/bin/env python
"""
Set the '_request' attribute of the client to a MagicMock object returning an empty dictionary.

This script defines a function 'test_remove_flag' that configures the '_request' attribute of the client object with a
MagicMock object that returns an empty dictionary.
It then invokes the 'remove_flag' method on the client object and verifies that the 'request' method was invoked with
specific arguments.

Arguments:
- client: An object representing a client used for making requests.

Side Effects:
- Updates the '_request' attribute of the client object.
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
