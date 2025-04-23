"""
This module contains unit tests for the functionality of a client that interacts with an issue tracking system,
specifically for listing issues based on various parameters.

The tests utilize mocking to simulate API responses for different scenarios, including filtering issues by assignee,
reporter, status, summary, and sprint conditions (both blocked and unblocked).

Functions:
- `mock_client_request(client, mock_return_value)`: Mocks the behavior of the client to return predefined responses for
specific API requests.
- `test_list_issues(client)`: Tests listing issues by assignee.
- `test_list_issues_reporter(client)`: Tests listing issues by reporter.
- `test_list_issues_with_status(client)`: Tests listing issues filtered by status.
- `test_list_issues_with_summary(client)`: Tests listing issues filtered by summary.
- `test_list_issues_with_blocked(client)`: Tests listing issues that are marked as blocked.
- `test_list_issues_with_unblocked(client)`: Tests listing issues that are marked as unblocked.
- `test_list_issues_with_none_sprints(client)`: Tests listing issues when the sprint field is None or missing.
- `test_list_issues_with_sprint_regex_matching(client)`: Tests listing issues with sprint data that matches a specific
regex pattern.

Each test asserts that the returned issues are in the expected format and contain the correct data.
"""

from unittest.mock import MagicMock

from core.env_fetcher import EnvFetcher


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

    # Mock the _request method to simulate an API response
    def mock_request(method, path, **kwargs):
        """
        Mock a request to a specified path with optional keyword arguments.

        Arguments:
        - method (str): The HTTP method used for the request.
        - path (str): The URL path to mock the request for.
        - **kwargs: Optional keyword arguments that can be used for customizing the request.

        Return:
        - mock_return_value: The value returned when the method is "GET" and the path contains "search".

        """

        if method == "GET" and "search" in path:
            return mock_return_value

    client._request = MagicMock(side_effect=mock_request)


def test_list_issues(client):
    """
    Retrieve a list of issues from a client.

    Arguments:
    - client: A client object used to make requests.

    Side Effects:
    - Calls the mock_client_request function with the client object and a dictionary containing a list of issues.

    """

    mock_client_request(client, {"issues": [{"key": "AAP-test_list_issues"}]})

    issues = client.list_issues(project="AAP", component="platform", assignee="user123")

    # Assert that the issues returned are a list and contain the correct key
    assert isinstance(issues, list)
    assert issues[0]["key"] == "AAP-test_list_issues"


def test_list_issues_reporter(client):
    """
    Retrieves a list of issues reported by a specific client.

    Arguments:
    - client (object): An object representing the client for whom the issues are being retrieved.

    Side Effects:
    - Calls the mock_client_request function with the provided client object and a dictionary containing a list of
    issues.

    """

    mock_client_request(client, {"issues": [{"key": "AAP-test_list_issues_reporter"}]})

    issues = client.list_issues(project="AAP", component="platform", reporter="user123")

    # Assert that the issues returned are a list and contain the correct key
    assert isinstance(issues, list)
    assert issues[0]["key"] == "AAP-test_list_issues_reporter"


def test_list_issues_with_status(client):
    """
    Retrieve a list of issues with a specific status from the client.

    Arguments:
    - client (object): The client object used to make requests.

    Side Effects:
    - Modifies the client by sending a request to retrieve a list of issues with a specific status.

    """

    mock_client_request(
        client, {"issues": [{"key": "AAP-test_list_issues_with_status"}]}
    )

    issues = client.list_issues(
        project="AAP", component="platform", assignee="user123", status="In Progress"
    )

    # Assert that the issues returned are a list and contain the correct key
    assert isinstance(issues, list)
    assert issues[0]["key"] == "AAP-test_list_issues_with_status"


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
        project="AAP", component="platform", assignee="user123", blocked=True
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
        project="AAP", component="platform", assignee="user123", unblocked=True
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
        Summary:
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

        if method == "GET" and "search" in path:
            # Return an issue with 'JIRA_SPRINT_FIELD' set to None or missing
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

    client._request = MagicMock(side_effect=mock_request)

    issues = client.list_issues(project="AAP", component="platform", assignee="user123")

    # Assert that the issues returned are a list and contain the correct key
    assert isinstance(issues, list)
    assert issues[0]["key"] == "AAP-test_list_issues_with_none_sprints"

    # Ensure that 'sprint' field is set to 'No active sprint' when sprints is None
    assert issues[0]["sprint"] == "No active sprint"


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
        represented by a dictionary with key, summary, status, assignee, priority, and custom JIRA fields like sprint
        data.

        Side Effects:
        - The function may interact with an external service to fetch JIRA issue data.

        Note:
        - This function is a mock implementation and does not actually perform a network request.
        """

        if method == "GET" and "search" in path:
            # Return an issue with JIRA_SPRINT_FIELD containing a sprint string
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

    client._request = MagicMock(side_effect=mock_request)

    issues = client.list_issues(project="AAP", component="platform", assignee="user123")

    # Assert that the issues returned are a list and contain the correct key
    # /* jscpd:ignore-start */
    assert isinstance(issues, list)
    assert issues[0]["key"] == "AAP-test_list_issues_with_sprint_regex_matching"
    # /* jscpd:ignore-end */
    # Ensure that the sprint is correctly extracted and assigned when sprint state is ACTIVE
    assert issues[0]["sprint"] == "SaaS Sprint 2025-13"  # Check the sprint name
