from jira.client import JiraClient


def test_list_issues(monkeypatch):
    client = JiraClient()

    monkeypatch.setattr(client, "get_current_user", lambda: "user123")

    def mock_request(method, path, **kwargs):
        if method == "GET" and "search" in path:
            return {"issues": [{"key": "AAP-1"}]}

    monkeypatch.setattr(client, "_request", mock_request)
    issues = client.list_issues(project="AAP", component="platform", assignee="user123")
    assert isinstance(issues, list)
    assert issues[0]["key"] == "AAP-1"
