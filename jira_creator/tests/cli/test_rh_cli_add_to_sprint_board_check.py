import pytest
from jira.client import JiraClient


def test_add_to_sprint_board_id_check():
    # Create the JiraClient instance
    client = JiraClient()

    # Mock the board_id attribute as None
    client.board_id = None

    # Check if the exception is raised when board_id is not set
    with pytest.raises(Exception, match="JIRA_BOARD_ID not set in environment"):
        client.add_to_sprint_by_name("AAP-1", "Sprint Alpha")
