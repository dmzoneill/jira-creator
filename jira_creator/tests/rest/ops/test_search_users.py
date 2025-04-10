from unittest.mock import MagicMock


def test_search_users_returns_expected_data(client):
    mock_users = [
        {"name": "daoneill", "displayName": "David O'Neill"},
        {"name": "jdoe", "displayName": "John Doe"},
    ]
    client._request = MagicMock(return_value=mock_users)

    results = client.search_users("daoneill")

    assert results == mock_users
    client._request.assert_called_once_with(
        "GET",
        "/rest/api/2/user/search",
        params={"username": "daoneill", "maxResults": 10},
    )
