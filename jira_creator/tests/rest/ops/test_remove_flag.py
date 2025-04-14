from unittest.mock import MagicMock


def test_remove_flag(client):
    client._request = MagicMock(return_value={})

    client.remove_flag("AAP-test_remove_flag")

    client._request.assert_called_once_with(
        "POST",
        "/rest/greenhopper/1.0/xboard/issue/flag/flag.json",
        json={"issueKeys": ["AAP-test_remove_flag"]},
    )
