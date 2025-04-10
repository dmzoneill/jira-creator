from unittest.mock import MagicMock


def test_get_user_returns_expected_data(client):
    mock_user = {
        "name": "daoneill",
        "displayName": "David O'Neill",
        "emailAddress": "daoneill@redhat.com",
    }
    client._request = MagicMock(return_value=mock_user)

    result = client.get_user("daoneill")

    assert result == mock_user
    client._request.assert_called_once_with(
        "GET", "/rest/api/2/user", params={"username": "daoneill"}
    )
