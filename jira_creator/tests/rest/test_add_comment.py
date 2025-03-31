from unittest.mock import MagicMock

from jira.client import JiraClient


def test_add_comment():
    client = JiraClient()
    client._request = MagicMock(return_value={})

    client.add_comment("AAP-123", "This is a comment")

    client._request.assert_called_once_with(
        "POST",
        "/rest/api/2/issue/AAP-123/comment",
        json={"body": "This is a comment"},
    )
