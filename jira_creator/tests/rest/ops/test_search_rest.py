#!/usr/bin/env python
"""
Unit tests for the JiraClient's search_issues method.

This module contains test cases designed to validate the functionality of the search_issues method in the JiraClient
class. It utilizes the unittest.mock library to mock the _request method, enabling controlled testing without actual
API calls.

The tests encompass various scenarios, including:
- Successful retrieval of issues associated with active sprints.
- Retrieval of issues when no sprints are associated.

Each test case verifies that the _request method is invoked with the correct parameters and checks that the output
matches expected values. The test functions are designed to simulate different responses from the Jira API to ensure
robust testing of the search_issues method's behavior.
"""

from unittest.mock import MagicMock

from core.env_fetcher import EnvFetcher

# /* jscpd:ignore-start */

fields = [
    {"id": "summary"},
    {"id": "status"},
    {"id": "assignee"},
    {"id": "priority"},
    {"id": EnvFetcher.get("JIRA_STORY_POINTS_FIELD")},
    {"id": EnvFetcher.get("JIRA_SPRINT_FIELD")},
    {"id": EnvFetcher.get("JIRA_BLOCKED_FIELD")},
]


def test_search_issues_multiple_calls(client):
    """
    Mock the _request method of JiraClient to simulate fetching issues from Jira, with multiple calls to different
    endpoints.

    Arguments:
    - client: A JiraClient object used to interact with the Jira API.

    Side Effects:
    - Modifies the behavior of the _request method of the provided JiraClient object by replacing it with a MagicMock
    object.

    This function tests handling of multiple requests within the search_issues method.
    """

    # Mock the _request method to simulate multiple calls to different endpoints
    client.request = MagicMock(
        side_effect=[
            # Mock for /rest/api/2/field
            fields,
            # Mock for /rest/api/2/search
            {
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
            },
        ]
    )

    # Execute the search_issues method with a sample JQL query
    jql = "project = AAP AND status = 'In Progress'"
    issues = client.search_issues(jql)

    # Assert that the _request method was called with the correct arguments for both requests
    # First request for fields
    client.request.assert_any_call("GET", "/rest/api/2/field")
    # Second request for search results
    client.request.assert_any_call(
        "GET",
        "/rest/api/2/search",
        params={
            "jql": jql,
            "fields": "summary,status,assignee,priority,"
            + EnvFetcher.get("JIRA_STORY_POINTS_FIELD")
            + ","
            + EnvFetcher.get("JIRA_SPRINT_FIELD")
            + ","
            + EnvFetcher.get("JIRA_BLOCKED_FIELD")
            + ",key",
            "maxResults": "200",
        },
    )

    # Assert that the method correctly processes the issue data
    assert issues[0]["key"] == "AAP-test_search_issues"
    assert (
        issues[0]["fields"]["sprint"] == "SaaS Sprint 2025-13"
    )  # Check if sprint name is parsed correctly


def test_search_issues_no_sprints_multiple_calls(client):
    """
    Simulate searching for Jira issues without any sprints and simulate multiple calls to different endpoints.

    Arguments:
    - client: An instance of JiraClient used to interact with the Jira API.

    Side Effects:
    - Modifies the _request method of the JiraClient by mocking it with a MagicMock to simulate no sprints in the
    response.
    """

    # Mock the _request method to simulate no sprints
    client.request = MagicMock(
        side_effect=[
            # Mock for /rest/api/2/field
            fields,
            # Mock for /rest/api/2/search with no sprints
            {
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
            },
        ]
    )

    # Execute the search_issues method with a sample JQL query
    jql = "project = AAP AND status = 'In Progress'"
    issues = client.search_issues(jql)

    # Assert that the _request method was called with the correct arguments for both requests
    # First request for fields
    client.request.assert_any_call("GET", "/rest/api/2/field")
    # Second request for search results
    client.request.assert_any_call(
        "GET",
        "/rest/api/2/search",
        params={
            "jql": jql,
            "fields": "summary,status,assignee,priority,"
            + EnvFetcher.get("JIRA_STORY_POINTS_FIELD")
            + ","
            + EnvFetcher.get("JIRA_SPRINT_FIELD")
            + ","
            + EnvFetcher.get("JIRA_BLOCKED_FIELD")
            + ",key",
            "maxResults": "200",
        },
    )

    # Assert that the sprint field is correctly set to 'No active sprint' when no sprints are found
    assert issues[0]["fields"]["sprint"] == "No active sprint"


# /* jscpd:ignore-end */
