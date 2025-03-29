from jira.client import JiraClient


def test_migrate_no_transitions(monkeypatch):
    client = JiraClient()

    def mock_request(method, path, **kwargs):
        if path.startswith("/rest/api/2/issue/AAP-1/transitions"):
            return {"transitions": []}
        elif path.startswith("/rest/api/2/issue/AAP-1"):
            return {"fields": {"summary": "Old", "description": "Old"}}
        elif path.startswith("/rest/api/2/issue/"):
            return {"key": "AAP-2"}

    monkeypatch.setattr(client, "_request", mock_request)
    monkeypatch.setattr(client, "jira_url", "http://fake")
    new_key = client.migrate_issue("AAP-1", "story")
    assert new_key == "AAP-2"
