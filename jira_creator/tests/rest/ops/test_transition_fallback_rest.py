from unittest.mock import MagicMock


def test_migrate_fallback_transition(client):
    transitions_called = []

    def mock_request(method, path, **kwargs):
        if "transitions" in path:
            transitions_called.append(True)
            return {"transitions": [{"name": "Something", "id": "99"}]}
        elif path.endswith("AAP-test_migrate_fallback_transition"):
            return {"fields": {"summary": "s", "description": "d"}}
        elif "comment" in path:
            return {}
        elif method == "POST":
            return {"key": "AAP-test_migrate_fallback_transition"}

    client._request = MagicMock(side_effect=mock_request)
    client.jira_url = "http://localhost"

    result = client.migrate_issue("AAP-test_migrate_fallback_transition", "task")

    assert result == "AAP-test_migrate_fallback_transition"
    assert transitions_called
