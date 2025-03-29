from jira.client import JiraClient


def test_vote_story_points(monkeypatch):
    client = JiraClient()
    monkeypatch.setattr(client, "_request", lambda *a, **kw: {"status": "ok"})
    monkeypatch.setenv("JIRA_STORY_POINT_FIELD", "customfield_99999")
    client.vote_story_points("AAP-100", 3)
