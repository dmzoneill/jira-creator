from unittest.mock import MagicMock

from core.env_fetcher import EnvFetcher


def mock_client_request(client, mock_return_value):
    # Mock get_current_user
    client.get_current_user = MagicMock(return_value="user123")

    # Mock the _request method to simulate an API response
    def mock_request(method, path, **kwargs):
        if method == "GET" and "search" in path:
            return mock_return_value

    client._request = MagicMock(side_effect=mock_request)


def test_list_issues(client):
    mock_client_request(client, {"issues": [{"key": "AAP-test_list_issues"}]})

    issues = client.list_issues(project="AAP", component="platform", assignee="user123")

    # Assert that the issues returned are a list and contain the correct key
    assert isinstance(issues, list)
    assert issues[0]["key"] == "AAP-test_list_issues"


def test_list_issues_reporter(client):
    mock_client_request(client, {"issues": [{"key": "AAP-test_list_issues_reporter"}]})

    issues = client.list_issues(project="AAP", component="platform", reporter="user123")

    # Assert that the issues returned are a list and contain the correct key
    assert isinstance(issues, list)
    assert issues[0]["key"] == "AAP-test_list_issues_reporter"


def test_list_issues_with_status(client):
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
    def mock_request(method, path, **kwargs):
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
    def mock_request(method, path, **kwargs):
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
