from unittest.mock import MagicMock

from core.env_fetcher import EnvFetcher


def test_search_issues(client):
    # Mock the _request method of JiraClient
    # /* jscpd:ignore-start */
    client._request = MagicMock(
        return_value={
            "issues": [
                {
                    "key": "AAP-test_search_issues",
                    "fields": {
                        "summary": "Run IQE tests in promotion pipelines",
                        "status": {"name": "In Progress"},
                        "assignee": {"displayName": "David O Neill"},
                        "priority": {"name": "Normal"},
                        EnvFetcher.get("JIRA_STORY_POINTS_FIELD"): 5,
                        EnvFetcher.get("JIRA_SPRINT_FIELD"): [
                            """com.atlassian.greenhopper.service.sprint.Sprint@5063ab17[id=70766,
                            rapidViewId=18242,state=ACTIVE,name=SaaS Sprint 2025-13,"
                            startDate=2025-03-27T12:01:00.000Z,endDate=2025-04-03T12:01:00.000Z]"""
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
            "fields": "summary,status,assignee,priority,"
            + EnvFetcher.get("JIRA_STORY_POINTS_FIELD")
            + ","
            + EnvFetcher.get("JIRA_SPRINT_FIELD")
            + ","
            + EnvFetcher.get("JIRA_BLOCKED_FIELD"),
            "maxResults": 200,
        },
    )
    # /* jscpd:ignore-end */

    # Assert that the method correctly processes the issue data
    assert issues[0]["key"] == "AAP-test_search_issues"
    assert (
        issues[0]["fields"]["sprint"] == "SaaS Sprint 2025-13"
    )  # Check if sprint name is parsed correctly


def test_search_issues_no_sprints(client):
    # Mock the _request method of JiraClient to simulate no sprints
    # /* jscpd:ignore-start */
    client._request = MagicMock(
        return_value={
            "issues": [
                {
                    "key": "AAP-test_search_issues_no_sprints",
                    "fields": {
                        "summary": "Run IQE tests in promotion pipelines",
                        "status": {"name": "In Progress"},
                        "assignee": {"displayName": "David O Neill"},
                        "priority": {"name": "Normal"},
                        EnvFetcher.get("JIRA_STORY_POINTS_FIELD"): 5,
                        EnvFetcher.get(
                            "JIRA_SPRINT_FIELD"
                        ): [],  # Empty list for no sprints
                    },
                }
            ]
        }
    )
    # /* jscpd:ignore-end */

    # Execute the search_issues method with a sample JQL query
    jql = "project = AAP AND status = 'In Progress'"
    issues = client.search_issues(jql)

    # Assert that the _request method was called with the correct arguments
    client._request.assert_called_once_with(
        "GET",
        "/rest/api/2/search",
        params={
            "jql": jql,
            "fields": "summary,status,assignee,priority,"
            + EnvFetcher.get("JIRA_STORY_POINTS_FIELD")
            + ","
            + EnvFetcher.get("JIRA_SPRINT_FIELD")
            + ","
            + EnvFetcher.get("JIRA_BLOCKED_FIELD"),
            "maxResults": 200,
        },
    )

    # Assert that the sprint field is correctly set to 'No active sprint' when no sprints are found
    assert issues[0]["fields"]["sprint"] == "No active sprint"
