from unittest.mock import MagicMock

from core.env_fetcher import EnvFetcher


def test_block_issue_calls_expected_fields(client):
    client._request = MagicMock()
    client.block_issue("ABC-123", "Waiting for dependency")

    payload = {}
    payload[EnvFetcher.get("JIRA_BLOCKED_FIELD")] = {"value": True}
    payload[EnvFetcher.get("JIRA_BLOCKED_REASON_FIELD")] = "Waiting for dependency"

    client._request.assert_called_once_with(
        "PUT",
        "/rest/api/2/issue/ABC-123",
        json=payload,
    )
