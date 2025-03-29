from jira.client import JiraClient
import pytest


def test_add_to_sprint_board_id_missing(monkeypatch):
    monkeypatch.delenv("JIRA_BOARD_ID", raising=False)
    with pytest.raises(EnvironmentError):
        JiraClient()
