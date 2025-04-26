#!/usr/bin/env python
"""
This script contains a test function to set the summary attribute of a client object to an empty dictionary using a
MagicMock object.

Function:
- test_set_summary(client): Sets the summary attribute of a client object to an empty dictionary using a MagicMock
object.

Arguments:
- client: A client object for which the summary attribute needs to be set.

Side Effects:
- Modifies the client object by setting its _request attribute to a MagicMock object.
"""
from unittest.mock import MagicMock


def test_set_summary(client):
    """
    Set the summary attribute of a client object to an empty dictionary using a MagicMock object.

    Arguments:
    - client: A client object for which the summary attribute needs to be set.

    Side Effects:
    - Modifies the client object by setting its _request attribute to a MagicMock object.
    """

    client.request = MagicMock(return_value={})

    client.set_summary("AAP-test_set_summary", "AAP-test_set_summary")

    client.request.assert_called_once_with(
        "PUT",
        "/rest/api/2/issue/AAP-test_set_summary",
        json_data={"fields": {"summary": "AAP-test_set_summary"}},
    )
