from jira.client import JiraClient
import pytest


def test_add_to_sprint_board_id_check(monkeypatch):
    client = JiraClient()
    client.board_id = None
    with pytest.raises(Exception, match="JIRA_BOARD_ID not set in environment"):
        client.add_to_sprint_by_name("AAP-1", "Sprint Alpha")
