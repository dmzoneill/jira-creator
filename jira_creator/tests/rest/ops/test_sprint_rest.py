from unittest.mock import MagicMock

from core.env_fetcher import EnvFetcher


def test_set_sprint(client):
    client._request = MagicMock(return_value={})

    client.set_sprint("AAP-test_set_sprint", 42)

    client._request.assert_called_once_with(
        "PUT",
        "/rest/api/2/issue/AAP-test_set_sprint",
        json={"fields": {EnvFetcher.get("JIRA_SPRINT_FIELD"): ["42"]}},
    )


def test_remove_from_sprint(client):
    client._request = MagicMock(return_value={})

    client.remove_from_sprint("AAP-test_remove_from_sprint")

    client._request.assert_called_once_with(
        "POST",
        "/rest/agile/1.0/backlog/issue",
        json={"issues": ["AAP-test_remove_from_sprint"]},  # Matching the actual call
    )
