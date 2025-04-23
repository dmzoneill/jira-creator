from unittest.mock import MagicMock


def test_add_flag(client):
    """
    Set a flag in the client for testing purposes.

    Arguments:
    - client: An instance of a client object to add the flag for testing.

    This function does not have a return value.
    """

    client._request = MagicMock(return_value={})

    issue_keys = "AAP-test_add_flag"
    client.add_flag(issue_keys)

    client._request.assert_called_once_with(
        "POST",
        "/rest/greenhopper/1.0/xboard/issue/flag/flag.json",
        json={"issueKeys": [issue_keys], "flag": True},
    )
