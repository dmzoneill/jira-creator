from jira.client import JiraClient
from unittest.mock import MagicMock


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
