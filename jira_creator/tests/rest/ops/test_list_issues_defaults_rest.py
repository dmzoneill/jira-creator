#!/usr/bin/env python
"""
This module contains unit tests for a client object, specifically designed to test API interactions related to issue
listing in a project management context. It includes a primary test function, `test_list_issues_defaults`, which
mocks the `get_current_user` method to simulate API requests for retrieving field data and a list of issues.

The module validates that the `list_issues` method correctly returns an empty list when no issues are available and
ensures that the appropriate API endpoints are called with the expected parameters. Key functionalities include
mocking user context, simulating API responses, and validating API call correctness through assertions.

Functions:
- test_list_issues_defaults(client): Tests the list_issues method of the client by mocking API calls and
verifying the expected behavior and interactions.
"""
from unittest.mock import MagicMock

from core.env_fetcher import EnvFetcher

# /* jscpd:ignore-start */


def test_list_issues_defaults(client):
    """
    Set up a mock for the get_current_user method in the provided client object to always return the string "me".
    This test will simulate two API calls: one for getting field data and another for getting the list of issues.
    Arguments:
    - client: An object representing the client to test.

    Side Effects:
    - Modifies the behavior of the get_current_user method in the client object by setting it to always return "me".
    - Mocks the _request method of the client to handle requests to /rest/api/2/field and /rest/api/2/search.

    No return value.
    """

    # Mock get_current_user to return a fixed user
    client.get_current_user = MagicMock(return_value="me")

    # Mock the _request method of the client to handle both /rest/api/2/field and /rest/api/2/search requests
    def mock_request(method, path, **kwargs):
        if method == "GET":
            if "/rest/api/2/field" in path:
                # Simulate the response for /rest/api/2/field
                return [
                    {"id": "summary"},
                    {"id": "status"},
                    {"id": "assignee"},
                    {"id": "priority"},
                    {"id": EnvFetcher.get("JIRA_STORY_POINTS_FIELD")},
                    {"id": EnvFetcher.get("JIRA_SPRINT_FIELD")},
                    {"id": EnvFetcher.get("JIRA_BLOCKED_FIELD")},
                ]
            elif "/rest/api/2/search" in path:
                # Simulate the response for /rest/api/2/search (empty list of issues)
                return {"issues": []}

    # Set the side_effect for the request method
    client.request = MagicMock(side_effect=mock_request)

    # Call list_issues and assert it returns an empty list
    result = client.list_issues()
    assert result == []

    # Assert that the _request method was called twice, once for fields and once for search
    assert client.request.call_count == 2

    fields = "summary,status,assignee,priority,customfield_12310243,customfield_12310940,customfield_12316543,key"
    jql = 'project="XYZ" AND component="backend" AND assignee="me" AND status NOT IN ("Closed", "Done", "Cancelled")'
    # Check the paths for each call
    client.request.assert_any_call("GET", "/rest/api/2/field")
    client.request.assert_any_call(
        "GET",
        "/rest/api/2/search",
        params={
            "maxResults": 200,
            "fields": fields,
            "jql": jql,
        },
    )

    # Ensure the request parameters are correct for both API calls
    # The first call for /rest/api/2/field should not have any query params
    client.request.assert_any_call("GET", "/rest/api/2/field")

    # The second call for /rest/api/2/search should have the correct JQL and maxResults
    fields = "summary,status,assignee,priority,customfield_12310243,customfield_12310940,customfield_12316543,key"
    jql = 'project="XYZ" AND component="backend" AND assignee="me" AND status NOT IN ("Closed", "Done", "Cancelled")'
    client.request.assert_any_call(
        "GET",
        "/rest/api/2/search",
        params={
            "maxResults": 200,
            "fields": fields,
            "jql": jql,
        },
    )


# /* jscpd:ignore-end */
