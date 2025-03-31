from unittest.mock import MagicMock

from jira.client import JiraClient


def test_lint_data_structure():
    client = JiraClient()

    issue_data = {
        "fields": {
            "summary": "",
            "description": None,
            "priority": None,
            "customfield_12310243": None,  # Story points
            "customfield_12316543": {"value": "True"},  # Blocked
            "customfield_12316544": "",  # Blocked reason
            "status": {"name": "In Progress"},
            "assignee": None,
        }
    }

    client._request = MagicMock(return_value=issue_data)
    result = client._request("GET", "/rest/api/2/issue/AAP-123")

    assert result["fields"]["status"]["name"] == "In Progress"
    assert result["fields"]["customfield_12316543"]["value"] == "True"
