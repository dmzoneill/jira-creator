import os
import pytest
from jira.client import JiraClient


@pytest.fixture
def mock_jira_env(monkeypatch):
    monkeypatch.setenv("JIRA_URL", "https://example.atlassian.net")
    monkeypatch.setenv("PROJECT_KEY", "XYZ")
    monkeypatch.setenv("AFFECTS_VERSION", "v1.2.3")
    monkeypatch.setenv("COMPONENT_NAME", "backend")
    monkeypatch.setenv("PRIORITY", "High")
    monkeypatch.setenv("JPAT", "dummy-token")


def test_build_payload(mock_jira_env):
    client = JiraClient()
    summary = "Fix login issue"
    description = "Steps to reproduce..."
    issue_type = "bug"

    payload = client.build_payload(summary, description, issue_type)
    fields = payload["fields"]

    assert fields["project"]["key"] == "XYZ"
    assert fields["summary"] == summary
    assert fields["description"] == description
    assert fields["issuetype"]["name"] == "Bug"
    assert fields["priority"]["name"] == "High"
    assert fields["versions"][0]["name"] == "v1.2.3"
    assert fields["components"][0]["name"] == "backend"


def test_missing_env(monkeypatch):
    monkeypatch.delenv("JPAT", raising=False)
    with pytest.raises(EnvironmentError):
        JiraClient()
