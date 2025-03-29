from jira.client import JiraClient


def test_epic_field(monkeypatch):
    monkeypatch.setenv("JIRA_EPIC_NAME_FIELD", "customfield_99999")
    client = JiraClient()
    result = client.build_payload("summary", "description", "epic")
    assert "customfield_99999" in result["fields"]
