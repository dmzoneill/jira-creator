from unittest.mock import MagicMock

from jira.client import JiraClient


def test_migrate_no_transitions():
    client = JiraClient()

    def mock_request(method, path, **kwargs):
        if path.startswith("/rest/api/2/issue/AAP-1/transitions"):
            return {"transitions": []}
        elif path.startswith("/rest/api/2/issue/AAP-1"):
            return {"fields": {"summary": "Old", "description": "Old"}}
        elif path.startswith("/rest/api/2/issue/"):
            return {"key": "AAP-2"}

    client._request = MagicMock(side_effect=mock_request)
    client.jira_url = "http://fake"

    new_key = client.migrate_issue("AAP-1", "story")
    assert new_key == "AAP-2"
