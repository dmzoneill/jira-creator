from unittest.mock import MagicMock

from jira.client import JiraClient


def test_set_sprint():
    client = JiraClient()
    client._request = MagicMock(return_value={})

    client.set_sprint("AAP-123", 42)

    client._request.assert_called_once_with(
        "PUT",
        "/rest/api/2/issue/AAP-123",
        json={"fields": {"customfield_12310940": ["42"]}},
    )


def test_remove_from_sprint():
    client = JiraClient()
    client._request = MagicMock(return_value={})

    client.remove_from_sprint("AAP-123")

    client._request.assert_called_once_with(
        "POST",
        "/rest/agile/1.0/backlog/issue",
        json={"issues": ["AAP-123"]},  # Matching the actual call
    )
