from jira.client import JiraClient


def test_change_issue_type(monkeypatch):
    client = JiraClient()

    def mock_request(method, path, **kwargs):
        if method == "GET":
            return {"fields": {"issuetype": {"subtask": True}}}
        return {}

    monkeypatch.setattr(client, "_request", mock_request)
    assert client.change_issue_type("AAP-1", "story")
