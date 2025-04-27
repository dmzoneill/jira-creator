#!/usr/bin/env python
"""
This module contains unit tests for a client interacting with an issue tracking system. The tests focus on
listing issues based on various parameters, including assignee, reporter, status, summary, and sprint
conditions (blocked and unblocked).

The tests utilize mocking to simulate API responses, ensuring that the client behaves correctly under
different scenarios. Each test verifies that the returned issues are formatted correctly and contain
the expected data.

Functions:
- `mock_client_request(client, mock_return_value)`: Mocks the client's API request behavior to return
predefined responses.
- `test_list_issues(client)`: Tests issue listing by assignee.
- `test_list_issues_reporter(client)`: Tests issue listing by reporter.
- `test_list_issues_with_status(client)`: Tests issue listing filtered by status.
- `test_list_issues_with_summary(client)`: Tests issue listing filtered by summary.
- `test_list_issues_with_blocked(client)`: Tests listing issues marked as blocked.
- `test_list_issues_with_unblocked(client)`: Tests listing issues marked as unblocked.
- `test_list_issues_with_none_sprints(client)`: Tests issue listing when sprint data is None or missing.
- `test_list_issues_with_sprint_regex_matching(client)`: Tests issue listing with sprint data matching
a specific regex pattern.
"""
import re
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


def mock_client_request(client, mock_return_value):
    """
    Mock the get_current_user method of a client object with a specified return value.

    Arguments:
    - client (object): The client object for which the get_current_user method will be mocked.
    - mock_return_value (any): The return value that the get_current_user method will be mocked to return.

    Side Effects:
    - Modifies the get_current_user method of the client object to return the specified mock_return_value.
    """

    # Mock get_current_user
    client.get_current_user = MagicMock(return_value="user123")

    # Mock the _request method to simulate an API response for both field and search requests
    def mock_request(method, path, **kwargs):
        """
        Mock a request to a specified path with optional keyword arguments.

        Arguments:
        - method (str): The HTTP method used for the request.
        - path (str): The URL path to mock the request for.
        - **kwargs: Optional keyword arguments that can be used for customizing the request.

        Return:
        - Different mock return values depending on the path and method.
        """

        if method == "GET":
            if "/rest/api/2/field" in path:
                # Return mock field data for /rest/api/2/field request
                return fields
            elif "/rest/api/2/search" in path:
                # Return the mock issue data for /rest/api/2/search request
                return mock_return_value

    client.request = MagicMock(side_effect=mock_request)


def test_list_issues(client):
    """
    Retrieve a list of issues from a client.

    Arguments:
    - client: A client object used to make requests.

    Side Effects:
    - Calls the mock_client_request function with the client object and a dictionary containing a list of issues.
    """

    # Mock the response of the second request (search issues)
    mock_client_request(client, {"issues": [{"key": "AAP-test_list_issues"}]})

    # Call the list_issues method and assert it returns the correct result
    issues = client.list_issues(project="AAP", component="platform", assignee="user123")

    # Assert that the issues returned are a list and contain the correct key
    assert isinstance(issues, list)
    assert issues[0]["key"] == "AAP-test_list_issues"

    # Assert that the _request method was called twice: once for the fields and once for the issues search
    assert client.request.call_count == 2
    jql = 'project="AAP" AND component="platform" AND assignee="user123"'
    jql += ' AND status NOT IN ("Closed", "Done", "Cancelled")'
    client.request.assert_any_call("GET", "/rest/api/2/field")
    client.request.assert_any_call(
        "GET",
        "/rest/api/2/search",
        params={
            "jql": jql,
            "maxResults": 200,
            "fields": "summary,status,assignee,priority,"
            + EnvFetcher.get("JIRA_STORY_POINTS_FIELD")
            + ","
            + EnvFetcher.get("JIRA_SPRINT_FIELD")
            + ","
            + EnvFetcher.get("JIRA_BLOCKED_FIELD")
            + ",key",
        },
    )


def test_list_issues_reporter(client):
    """
    Retrieves a list of issues reported by a specific client.

    Arguments:
    - client (object): An object representing the client for whom the issues are being retrieved.

    Side Effects:
    - Calls the mock_client_request function with the provided client object and a dictionary containing a list of
    issues.
    """

    def mock_request(method, path, **kwargs):
        if method == "GET":
            if "/rest/api/2/field" in path:
                # Mock the response for /rest/api/2/field
                return fields
            elif "/rest/api/2/search" in path:
                # Mock the response for /rest/api/2/search with issues reported by "user123"
                return {"issues": [{"key": "AAP-test_list_issues_reporter"}]}

    # Set the mock request to simulate multiple API calls
    client.request = MagicMock(side_effect=mock_request)

    # Call the list_issues method and assert it returns the correct result
    issues = client.list_issues(project="AAP", component="platform", reporter="user123")

    # Assert that the issues returned are a list and contain the correct key
    assert isinstance(issues, list)
    assert issues[0]["key"] == "AAP-test_list_issues_reporter"

    # Assert that the _request method was called twice: once for fields and once for the search
    assert client.request.call_count == 2
    jql = 'project="AAP" AND component="platform" AND reporter="user123"'
    jql += ' AND status NOT IN ("Closed", "Done", "Cancelled")'
    client.request.assert_any_call("GET", "/rest/api/2/field")
    client.request.assert_any_call(
        "GET",
        "/rest/api/2/search",
        params={
            "jql": jql,
            "maxResults": 200,
            "fields": "summary,status,assignee,priority,"
            + EnvFetcher.get("JIRA_STORY_POINTS_FIELD")
            + ","
            + EnvFetcher.get("JIRA_SPRINT_FIELD")
            + ","
            + EnvFetcher.get("JIRA_BLOCKED_FIELD")
            + ",key",
        },
    )


def test_list_issues_with_status(client):
    """
    Retrieve a list of issues with a specific status from the client.

    Arguments:
    - client (object): The client object used to make requests.

    Side Effects:
    - Modifies the client by sending a request to retrieve a list of issues with a specific status.
    """

    def mock_request(method, path, **kwargs):
        if method == "GET":
            if "/rest/api/2/field" in path:
                # Mock the response for /rest/api/2/field
                return fields
            elif "/rest/api/2/search" in path:
                # Mock the response for /rest/api/2/search with status "In Progress"
                return {"issues": [{"key": "AAP-test_list_issues_with_status"}]}

    # Set the mock request to simulate multiple API calls
    client.request = MagicMock(side_effect=mock_request)

    # Call the list_issues method and assert it returns the correct result
    issues = client.list_issues(
        project="AAP", component="platform", assignee="user123", status="In Progress"
    )

    # Assert that the issues returned are a list and contain the correct key
    assert isinstance(issues, list)
    assert issues[0]["key"] == "AAP-test_list_issues_with_status"

    # Assert that the _request method was called twice: once for fields and once for the search
    assert client.request.call_count == 2
    jql = 'project="AAP" AND component="platform" AND assignee="user123"'
    jql += ' AND status="In Progress" AND status NOT IN ("Closed", "Done", "Cancelled")'
    client.request.assert_any_call("GET", "/rest/api/2/field")
    client.request.assert_any_call(
        "GET",
        "/rest/api/2/search",
        params={
            "jql": jql,
            "maxResults": 200,
            "fields": "summary,status,assignee,priority,"
            + EnvFetcher.get("JIRA_STORY_POINTS_FIELD")
            + ","
            + EnvFetcher.get("JIRA_SPRINT_FIELD")
            + ","
            + EnvFetcher.get("JIRA_BLOCKED_FIELD")
            + ",key",
        },
    )


def test_list_issues_with_summary(client):
    """
    Retrieve a list of issues from a client and check for a specific summary.

    Arguments:
    - client (object): The client object used to make requests.

    Side Effects:
    - Calls the mock_client_request function to retrieve a list of issues with a specific key.
    """

    mock_client_request(
        client, {"issues": [{"key": "AAP-test_list_issues_with_summary"}]}
    )

    issues = client.list_issues(
        project="AAP", component="platform", assignee="user123", summary="Onboarding"
    )

    # Assert that the issues returned are a list and contain the correct key
    assert isinstance(issues, list)
    assert issues[0]["key"] == "AAP-test_list_issues_with_summary"


def test_list_issues_with_blocked(client):
    """
    Retrieve a list of issues with a specific key from the client.

    Arguments:
    - client (object): The client object used to make requests.

    Side Effects:
    - Modifies the client by requesting a list of issues with a specific key.
    """

    mock_client_request(
        client, {"issues": [{"key": "AAP-test_list_issues_with_blocked"}]}
    )

    issues = client.list_issues(
        project="AAP", component="platform", assignee="user123", issues_blocked=True
    )

    # Assert that the issues returned are a list and contain the correct key
    assert isinstance(issues, list)
    assert issues[0]["key"] == "AAP-test_list_issues_with_blocked"

    mock_client_request(
        client, {"issues": [{"key": "AAP-test_list_issues_with_blocked"}]}
    )


def test_list_issues_with_unblocked(client):
    """
    Retrieve and list all unblocked issues for a specific client.

    Arguments:
    - client (object): The client object used to make requests.

    Side Effects:
    - Calls the mock_client_request function to retrieve a list of issues for the specified client.
    """

    mock_client_request(
        client, {"issues": [{"key": "AAP-test_list_issues_with_unblocked"}]}
    )

    issues = client.list_issues(
        project="AAP", component="platform", assignee="user123", issues_unblocked=True
    )

    assert isinstance(issues, list)
    assert issues[0]["key"] == "AAP-test_list_issues_with_unblocked"

    mock_client_request(
        client, {"issues": [{"key": "AAP-test_list_issues_with_unblocked"}]}
    )


def test_list_issues_with_none_sprints(client):
    """
    Retrieve and display a list of issues from a client's system that are not assigned to any sprint.

    Arguments:
    - client (Client): An object representing the client's system to fetch the list of issues from.

    This function does not return any value.

    Exceptions:
    - None
    """

    def mock_request(method, path, **kwargs):
        """
        Simulates a mock request to a server with the provided HTTP method and path. If the method is 'GET' and the
        path contains 'search', it returns mock data for an issue with specific fields set.

        Arguments:
        - method (str): The HTTP method of the request.
        - path (str): The path of the request.
        - **kwargs: Additional keyword arguments that are not used in the current implementation.

        Return:
        A dictionary containing mock data for an issue with fields like key, summary, status, assignee, priority, and
        specific values for 'JIRA_STORY_POINTS_FIELD' and 'JIRA_SPRINT_FIELD'. The 'JIRA_SPRINT_FIELD' is set to None
        to indicate missing sprints data.

        Side Effects:
        None
        """

        if method == "GET":
            if "/rest/api/2/field" in path:
                # Mock the response for /rest/api/2/field
                return fields
            elif "/rest/api/2/search" in path:
                # Mock the response for /rest/api/2/search with 'JIRA_SPRINT_FIELD' set to None
                return {
                    "issues": [
                        {
                            "key": "AAP-test_list_issues_with_none_sprints",
                            "fields": {
                                "summary": "Run IQE tests in promotion pipelines",
                                "status": {"name": "In Progress"},
                                "assignee": {"displayName": "David O Neill"},
                                "priority": {"name": "Normal"},
                                EnvFetcher.get("JIRA_STORY_POINTS_FIELD"): 5,
                                EnvFetcher.get(
                                    "JIRA_SPRINT_FIELD"
                                ): None,  # No sprints data
                            },
                        }
                    ]
                }

    # Set the side_effect for the request method
    client.request = MagicMock(side_effect=mock_request)

    # Call the list_issues method and assert it returns the correct result
    issues = client.list_issues(project="AAP", component="platform", assignee="user123")

    # Assert that the issues returned are a list and contain the correct key
    assert isinstance(issues, list)
    assert issues[0]["key"] == "AAP-test_list_issues_with_none_sprints"

    # Ensure that 'sprint' field is set to 'No active sprint' when sprints is None
    assert issues[0]["sprint"] == "No active sprint"

    # Assert that the _request method was called twice, once for fields and once for search
    assert client.request.call_count == 2

    jql = 'project="AAP" AND component="platform" AND '
    jql += 'assignee="user123" AND status NOT IN ("Closed", "Done", "Cancelled")'
    client.request.assert_any_call("GET", "/rest/api/2/field")
    client.request.assert_any_call(
        "GET",
        "/rest/api/2/search",
        params={
            "jql": jql,
            "maxResults": 200,
            "fields": "summary,status,assignee,priority,"
            + EnvFetcher.get("JIRA_STORY_POINTS_FIELD")
            + ","
            + EnvFetcher.get("JIRA_SPRINT_FIELD")
            + ","
            + EnvFetcher.get("JIRA_BLOCKED_FIELD")
            + ",key",
        },
    )


def test_list_issues_with_sprint_regex_matching(client):
    """
    Check for issues in a list that match a sprint regex pattern.

    Arguments:
    - client (object): An object representing the client connection to Jira.

    Exceptions:
    - None
    """

    def mock_request(method, path, **kwargs):
        """
        Simulate a mock request to retrieve issues with specific criteria from a JIRA-like system.

        Arguments:
        - method (str): The HTTP method used for the request (e.g., "GET", "POST").
        - path (str): The path of the request, which may contain search parameters.
        - **kwargs: Additional keyword arguments that may be provided but are not used in the current implementation.

        Return:
        - dict: A dictionary containing the retrieved issues that match the specified criteria. Each issue is
        represented by a dictionary with keys: summary, status, assignee, priority, and custom JIRA fields like sprint
        data.

        Side Effects:
        - The function may interact with an external service to fetch JIRA issue data.

        Note:
        - This function is a mock implementation and does not actually perform a network request.
        """

        if method == "GET":
            if "/rest/api/2/field" in path:
                # Simulate the response for /rest/api/2/field
                return fields
            elif "/rest/api/2/search" in path:
                # Simulate the response for /rest/api/2/search with issues containing sprint data
                return {
                    "issues": [
                        {
                            "key": "AAP-test_list_issues_with_sprint_regex_matching",
                            "fields": {
                                "summary": "Run IQE tests in promotion pipelines",
                                "status": {"name": "In Progress"},
                                "assignee": {"displayName": "David O Neill"},
                                "priority": {"name": "Normal"},
                                EnvFetcher.get("JIRA_STORY_POINTS_FIELD"): 5,
                                EnvFetcher.get("JIRA_SPRINT_FIELD"): [
                                    """com.atlassian.greenhopper.service.sprint.Sprint@5063ab17[id=70766,rapidViewId=18242,
                                    state=ACTIVE,name=SaaS Sprint 2025-13,startDate=2025-03-27T12:01:00.000Z,"
                                    endDate=2025-04-03T12:01:00.000Z]"""
                                ],  # Sprint data with ACTIVE state
                            },
                        }
                    ]
                }

    # Set the side_effect for the request method
    client.request = MagicMock(side_effect=mock_request)

    # Call the list_issues method and assert it returns the correct result
    issues = client.list_issues(project="AAP", component="platform", assignee="user123")

    # Assert that the issues returned are a list and contain the correct key
    assert isinstance(issues, list)
    assert issues[0]["key"] == "AAP-test_list_issues_with_sprint_regex_matching"

    # Ensure that the sprint is correctly extracted and assigned when sprint state is ACTIVE
    sprint_data = issues[0]["fields"][EnvFetcher.get("JIRA_SPRINT_FIELD")]
    name_regex = r"name\s*=\s*([^,]+)"  # Regex to capture sprint name
    sprint_name = None

    for sprint_str in sprint_data:
        match = re.search(name_regex, sprint_str)
        if match:
            sprint_name = match.group(1)
            break

    assert (
        sprint_name == "SaaS Sprint 2025-13"
    )  # Check if the sprint name matches the expected value

    # Assert that the _request method was called twice, once for fields and once for search
    assert client.request.call_count == 2

    jql = 'project="AAP" AND component="platform" AND assignee="user123"'
    jql += ' AND status NOT IN ("Closed", "Done", "Cancelled")'
    client.request.assert_any_call("GET", "/rest/api/2/field")
    client.request.assert_any_call(
        "GET",
        "/rest/api/2/search",
        params={
            "jql": jql,
            "maxResults": 200,
            "fields": "summary,status,assignee,priority,"
            + EnvFetcher.get("JIRA_STORY_POINTS_FIELD")
            + ","
            + EnvFetcher.get("JIRA_SPRINT_FIELD")
            + ","
            + EnvFetcher.get("JIRA_BLOCKED_FIELD")
            + ",key",
        },
    )


# /* jscpd:ignore-end */
