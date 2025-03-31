from unittest.mock import MagicMock

from jira.client import JiraClient


def test_search_issues():
    # Create an instance of JiraClient
    client = JiraClient()

    # Mock the _request method of JiraClient
    client._request = MagicMock(
        return_value={
            "issues": [
                {
                    "key": "AAP-41844",
                    "fields": {
                        "summary": "Run IQE tests in promotion pipelines",
                        "status": {"name": "In Progress"},
                        "assignee": {"displayName": "David O Neill"},
                        "priority": {"name": "Normal"},
                        "customfield_12310243": 5,
                        "customfield_12310940": [
                            "com.atlassian.greenhopper.service.sprint.Sprint@5063ab17[id=70766,rapidViewId=18242,state=ACTIVE,name=SaaS Sprint 2025-13,startDate=2025-03-27T12:01:00.000Z,endDate=2025-04-03T12:01:00.000Z]"
                        ],
                    },
                }
            ]
        }
    )

    # Execute the search_issues method with a sample JQL query
    jql = "project = AAP AND status = 'In Progress'"
    issues = client.search_issues(jql)

    # Assert that the _request method was called with the correct arguments
    client._request.assert_called_once_with(
        "GET",
        "/rest/api/2/search",
        params={
            "jql": jql,
            "fields": "summary,status,assignee,priority,customfield_12310243,customfield_12310940,customfield_12316543",
            "maxResults": 200,
        },
    )

    # Assert that the method correctly processes the issue data
    assert issues[0]["key"] == "AAP-41844"
    assert (
        issues[0]["fields"]["sprint"] == "SaaS Sprint 2025-13"
    )  # Check if sprint name is parsed correctly


def test_search_issues_no_sprints():
    # Create an instance of JiraClient
    client = JiraClient()

    # Mock the _request method of JiraClient to simulate no sprints
    client._request = MagicMock(
        return_value={
            "issues": [
                {
                    "key": "AAP-41844",
                    "fields": {
                        "summary": "Run IQE tests in promotion pipelines",
                        "status": {"name": "In Progress"},
                        "assignee": {"displayName": "David O Neill"},
                        "priority": {"name": "Normal"},
                        "customfield_12310243": 5,
                        "customfield_12310940": [],  # Empty list for no sprints
                    },
                }
            ]
        }
    )

    # Execute the search_issues method with a sample JQL query
    jql = "project = AAP AND status = 'In Progress'"
    issues = client.search_issues(jql)

    # Assert that the _request method was called with the correct arguments
    client._request.assert_called_once_with(
        "GET",
        "/rest/api/2/search",
        params={
            "jql": jql,
            "fields": "summary,status,assignee,priority,customfield_12310243,customfield_12310940,customfield_12316543",
            "maxResults": 200,
        },
    )

    # Assert that the sprint field is correctly set to 'No active sprint' when no sprints are found
    assert issues[0]["fields"]["sprint"] == "No active sprint"
