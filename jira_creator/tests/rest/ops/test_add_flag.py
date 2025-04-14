from unittest.mock import MagicMock


def test_add_flag(client):
    client._request = MagicMock(return_value={})

    issue_keys = ["AAP-test_add_flag"]
    client.add_flag(issue_keys)

    client._request.assert_called_once_with(
        "POST",
        "/rest/greenhopper/1.0/xboard/issue/flag/flag.json",
        json={"issueKeys": issue_keys, "flag": True},
    )
