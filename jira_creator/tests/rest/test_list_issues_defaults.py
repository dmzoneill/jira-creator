from unittest.mock import MagicMock

from jira.client import JiraClient


def test_list_issues_defaults():
    client = JiraClient()

    # Mock get_current_user to return a fixed user
    client.get_current_user = MagicMock(return_value="me")

    # Mock _request to return an empty issue list
    client._request = MagicMock(return_value={"issues": []})

    # Call list_issues and assert it returns an empty list
    result = client.list_issues()
    assert result == []
