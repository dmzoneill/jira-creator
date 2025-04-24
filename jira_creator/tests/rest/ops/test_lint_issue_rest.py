#!/usr/bin/env python
"""
This script defines a unit test function test_lint_data_structure(client) that tests the data structure of an issue in
a JIRA system. The function uses a MagicMock object to simulate the response from a client request to a specific JIRA
issue. It then performs assertions to validate certain fields in the issue data, such as the status and blocked fields.
The test ensures that the status field's name is "In Progress" and the blocked field's value is "True". The test is
designed to be run within a testing framework that supports mocking client requests.

test_lint_data_structure(client):
Lint the data structure of an issue before sending it to a client.

Arguments:
- client (Client): The client object to which the issue data will be sent.

Side Effects:
- Modifies the issue_data dictionary structure to ensure it meets certain requirements before being sent to the
client.
"""

from unittest.mock import MagicMock

from core.env_fetcher import EnvFetcher


def test_lint_data_structure(client):
    """
    Lint the data structure of an issue before sending it to a client.

    Arguments:
    - client (Client): The client object to which the issue data will be sent.

    Side Effects:
    - Modifies the issue_data dictionary structure to ensure it meets certain requirements before being sent to the
    client.
    """

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

    client.request = MagicMock(return_value=issue_data)
    result = client.request("GET", "/rest/api/2/issue/AAP-test_lint_data_structure")

    assert result["fields"]["status"]["name"] == "In Progress"
    assert result["fields"][EnvFetcher.get("JIRA_BLOCKED_FIELD")]["value"] == "True"
