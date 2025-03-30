from jira.client import JiraClient
from unittest.mock import MagicMock


def test_get_current_user():
    client = JiraClient()
    client._request = MagicMock(return_value={"name": "user123"})

    assert client.get_current_user() == "user123"
