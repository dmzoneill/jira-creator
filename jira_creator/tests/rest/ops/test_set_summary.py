from unittest.mock import MagicMock


def test_set_summary(client):
    client._request = MagicMock(return_value={})

    client.set_summary("AAP-test_set_summary")

    client._request.assert_called_once_with(
        "POST",
        "/rest/api/2/issue/AAP-test_set_summary",
        json={},
    )
