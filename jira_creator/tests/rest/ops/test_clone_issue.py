from unittest.mock import MagicMock


def test_clone_issue(client):
    client._request = MagicMock(return_value={})

    client.clone_issue("AAP-test_clone_issue")

    client._request.assert_called()
