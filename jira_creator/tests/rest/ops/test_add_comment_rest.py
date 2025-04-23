from unittest.mock import MagicMock


def test_add_comment(client):
    """
    Sets the return value of the _request method of the client to an empty dictionary when called.

    Arguments:
    - client: An instance of a client object.

    Side Effects:
    - Modifies the return value of the _request method of the client to an empty dictionary.
    """

    client._request = MagicMock(return_value={})

    client.add_comment("AAP-test_add_comment", "This is a comment")

    client._request.assert_called_once_with(
        "POST",
        "/rest/api/2/issue/AAP-test_add_comment/comment",
        json={"body": "This is a comment"},
    )
