from jira.client import JiraClient



def test_set_story_points(monkeypatch):
    called = {}

    def fake_request(method, path, json=None, allow_204=False, **kwargs):
        called.update({
            "method": method,
            "path": path,
            "json": json,
            "allow_204": allow_204
        })
        return {}

    monkeypatch.setenv("JIRA_STORY_POINT_FIELD", "customfield_99999")
    client = JiraClient()
    monkeypatch.setattr(client, "_request", fake_request)

    client.set_story_points("AAP-123", 8)

    assert called["method"] == "PUT"
    assert called["path"] == "/rest/api/2/issue/AAP-123"
    assert called["allow_204"] is True
    assert called["json"] == {"fields": {"customfield_99999": 8}}
