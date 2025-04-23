from unittest.mock import MagicMock


def test_clone_issue(client):
    """
    Clones an issue using the provided client.

    Arguments:
    - client: An object representing the client used to interact with the issue system.

    Side Effects:
    - Modifies the client's `_request` attribute by setting it to a MagicMock object.

    """

    client._request = MagicMock(return_value={})

    client.clone_issue("AAP-test_clone_issue")

    client._request.assert_called()
