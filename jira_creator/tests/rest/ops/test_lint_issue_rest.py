from unittest.mock import MagicMock

from core.env_fetcher import EnvFetcher


def test_lint_data_structure(client):
    issue_data = {
        "fields": {
            "summary": "",
            "description": None,
            "priority": None,
            EnvFetcher.get("JIRA_STORY_POINTS_FIELD"): None,  # Story points
            EnvFetcher.get("JIRA_BLOCKED_FIELD"): {"value": "True"},  # Blocked
            EnvFetcher.get("JIRA_BLOCKED_REASON_FIELD"): "",  # Blocked reason
            "status": {"name": "In Progress"},
            "assignee": None,
        }
    }

    client._request = MagicMock(return_value=issue_data)
    result = client._request("GET", "/rest/api/2/issue/AAP-test_lint_data_structure")

    assert result["fields"]["status"]["name"] == "In Progress"
    assert result["fields"][EnvFetcher.get("JIRA_BLOCKED_FIELD")]["value"] == "True"
