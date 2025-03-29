from jira.client import JiraClient


def test_add_comment(monkeypatch):
    client = JiraClient()
    called = {}

    def mock_request(method, path, json=None, **kwargs):
        called["method"] = method
        called["path"] = path
        called["body"] = json["body"]
        return {}

    monkeypatch.setattr(client, "_request", mock_request)
    client.add_comment("AAP-123", "This is a comment")
    assert called["method"] == "POST"
    assert called["path"] == "/rest/api/2/issue/AAP-123/comment"
    assert called["body"] == "This is a comment"
