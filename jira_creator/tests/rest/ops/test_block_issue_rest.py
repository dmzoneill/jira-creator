from unittest.mock import MagicMock


def test_block_issue_calls_expected_fields(client):
    client._request = MagicMock()
    client.block_issue("ABC-123", "Waiting for dependency")

    client._request.assert_called_once_with(
        "PUT",
        "/rest/api/2/issue/ABC-123",
        json={
            "fields": {
                "customfield_12316543": {"value": "True"},
                "customfield_12316544": "Waiting for dependency",
            }
        },
    )
