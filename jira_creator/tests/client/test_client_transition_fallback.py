from unittest.mock import MagicMock

from jira.client import JiraClient


def test_migrate_fallback_transition():
    client = JiraClient()
    transitions_called = []

    def mock_request(method, path, **kwargs):
        if "transitions" in path:
            transitions_called.append(True)
            return {"transitions": [{"name": "Something", "id": "99"}]}
        elif path.endswith("AAP-1"):
            return {"fields": {"summary": "s", "description": "d"}}
        elif "comment" in path:
            return {}
        elif method == "POST":
            return {"key": "AAP-2"}

    client._request = MagicMock(side_effect=mock_request)
    client.jira_url = "http://localhost"

    result = client.migrate_issue("AAP-1", "task")

    assert result == "AAP-2"
    assert transitions_called
