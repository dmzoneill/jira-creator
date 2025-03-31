from unittest.mock import MagicMock

from jira.client import JiraClient


def test_list_issues():
    client = JiraClient()

    # Mock get_current_user
    client.get_current_user = MagicMock(return_value="user123")

    # Mock the _request method to simulate an API response
    def mock_request(method, path, **kwargs):
        if method == "GET" and "search" in path:
            return {"issues": [{"key": "AAP-1"}]}

    client._request = MagicMock(side_effect=mock_request)

    issues = client.list_issues(project="AAP", component="platform", assignee="user123")

    # Assert that the issues returned are a list and contain the correct key
    assert isinstance(issues, list)
    assert issues[0]["key"] == "AAP-1"


def test_list_issues_with_status():
    client = JiraClient()

    # Mock get_current_user to return a fixed user
    client.get_current_user = MagicMock(return_value="user123")

    # Mock the _request method to simulate an API response
    def mock_request(method, path, **kwargs):
        if method == "GET" and "search" in path:
            # Verify the JQL query contains the status condition
            jql = kwargs.get("params", {}).get("jql", "")
            assert (
                'status="In Progress"' in jql
            ), f"Expected status='In Progress' in JQL, but got {jql}"
            return {"issues": [{"key": "AAP-1"}]}

    client._request = MagicMock(side_effect=mock_request)

    # Call list_issues with the status argument
    issues = client.list_issues(
        project="AAP", component="platform", assignee="user123", status="In Progress"
    )

    # Assert that the issues returned are a list and contain the correct key
    assert isinstance(issues, list)
    assert issues[0]["key"] == "AAP-1"


def test_list_issues_with_summary():
    client = JiraClient()

    # Mock get_current_user to return a fixed user
    client.get_current_user = MagicMock(return_value="user123")

    # Mock the _request method to simulate an API response
    def mock_request(method, path, **kwargs):
        if method == "GET" and "search" in path:
            # Verify the JQL query contains the summary condition
            jql = kwargs.get("params", {}).get("jql", "")
            assert (
                'summary~"Onboarding"' in jql
            ), f"Expected summary='Onboarding' in JQL, but got {jql}"
            return {"issues": [{"key": "AAP-1"}]}

    client._request = MagicMock(side_effect=mock_request)

    # Call list_issues with the summary argument
    issues = client.list_issues(
        project="AAP", component="platform", assignee="user123", summary="Onboarding"
    )

    # Assert that the issues returned are a list and contain the correct key
    assert isinstance(issues, list)
    assert issues[0]["key"] == "AAP-1"


def test_list_issues_with_blocked_unblocked():
    client = JiraClient()

    # Mock get_current_user to return a fixed user
    client.get_current_user = MagicMock(return_value="user123")

    # Mock the _request method to simulate an API response
    def mock_request(method, path, **kwargs):
        if method == "GET" and "search" in path:
            # Verify the JQL query contains the blocked condition
            jql = kwargs.get("params", {}).get("jql", "")
            assert (
                'customfield_12316543="True"' in jql
            ), f"Expected customfield_12316543='True' in JQL, but got {jql}"
            assert (
                'customfield_12316543!="True"' not in jql
            ), f"Unexpected customfield_12316543!='True' in JQL, got {jql}"
            return {"issues": [{"key": "AAP-1"}]}

    client._request = MagicMock(side_effect=mock_request)

    # Call list_issues with the blocked argument
    issues = client.list_issues(
        project="AAP", component="platform", assignee="user123", blocked=True
    )

    # Assert that the issues returned are a list and contain the correct key
    assert isinstance(issues, list)
    assert issues[0]["key"] == "AAP-1"

    # Test for unblocked argument
    def mock_request_unblocked(method, path, **kwargs):
        if method == "GET" and "search" in path:
            # Verify the JQL query contains the unblocked condition
            jql = kwargs.get("params", {}).get("jql", "")
            assert (
                'customfield_12316543!="True"' in jql
            ), f"Expected customfield_12316543!='True' in JQL, but got {jql}"
            assert (
                'customfield_12316543="True"' not in jql
            ), f"Unexpected customfield_12316543='True' in JQL, got {jql}"
            return {"issues": [{"key": "AAP-1"}]}

    client._request = MagicMock(side_effect=mock_request_unblocked)

    # Call list_issues with the unblocked argument
    issues_unblocked = client.list_issues(
        project="AAP", component="platform", assignee="user123", unblocked=True
    )

    # Assert that the issues returned are a list and contain the correct key
    assert isinstance(issues_unblocked, list)
    assert issues_unblocked[0]["key"] == "AAP-1"


def test_list_issues_with_none_sprints():
    client = JiraClient()

    # Mock get_current_user to return a fixed user
    client.get_current_user = MagicMock(return_value="user123")

    # Mock the _request method to simulate an issue with no sprints
    def mock_request(method, path, **kwargs):
        if method == "GET" and "search" in path:
            # Return an issue with 'customfield_12310940' set to None or missing
            return {
                "issues": [
                    {
                        "key": "AAP-41844",
                        "fields": {
                            "summary": "Run IQE tests in promotion pipelines",
                            "status": {"name": "In Progress"},
                            "assignee": {"displayName": "David O Neill"},
                            "priority": {"name": "Normal"},
                            "customfield_12310243": 5,
                            "customfield_12310940": None,  # No sprints data
                        },
                    }
                ]
            }

    client._request = MagicMock(side_effect=mock_request)

    # Call list_issues with no sprints data
    issues = client.list_issues(project="AAP", component="platform", assignee="user123")

    # Assert that the issues returned are a list and contain the correct key
    assert isinstance(issues, list)
    assert issues[0]["key"] == "AAP-41844"

    # Ensure that 'sprint' field is set to 'No active sprint' when sprints is None
    assert issues[0]["sprint"] == "No active sprint"


def test_list_issues_with_sprint_regex_matching():
    client = JiraClient()

    # Mock get_current_user to return a fixed user
    client.get_current_user = MagicMock(return_value="user123")

    # Mock the _request method to simulate an issue with sprints data
    def mock_request(method, path, **kwargs):
        if method == "GET" and "search" in path:
            # Return an issue with customfield_12310940 containing a sprint string
            return {
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
                            ],  # Sprint data with ACTIVE state
                        },
                    }
                ]
            }

    client._request = MagicMock(side_effect=mock_request)

    # Call list_issues with sprint data
    issues = client.list_issues(project="AAP", component="platform", assignee="user123")

    # Assert that the issues returned are a list and contain the correct key
    assert isinstance(issues, list)
    assert issues[0]["key"] == "AAP-41844"

    # Ensure that the sprint is correctly extracted and assigned when sprint state is ACTIVE
    assert issues[0]["sprint"] == "SaaS Sprint 2025-13"  # Check the sprint name
