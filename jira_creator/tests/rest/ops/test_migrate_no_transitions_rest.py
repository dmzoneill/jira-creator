from unittest.mock import MagicMock


def test_migrate_no_transitions(client):
    def mock_request(method, path, **kwargs):
        if path.startswith(
            "/rest/api/2/issue/AAP-test_migrate_no_transitions/transitions"
        ):
            return {"transitions": []}
        elif path.startswith("/rest/api/2/issue/AAP-test_migrate_no_transitions"):
            return {"fields": {"summary": "Old", "description": "Old"}}
        elif path.startswith("/rest/api/2/issue/"):
            return {"key": "AAP-test_migrate_no_transitions"}

    client._request = MagicMock(side_effect=mock_request)
    client.jira_url = "http://fake"

    new_key = client.migrate_issue("AAP-test_migrate_no_transitions", "story")
    assert new_key == "AAP-test_migrate_no_transitions"
