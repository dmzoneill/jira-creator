import pytest


def test_add_to_sprint_board_id_check(client):
    # Mock the board_id attribute as None
    client.board_id = None

    # Check if the exception is raised when board_id is not set
    with pytest.raises(Exception, match="JIRA_BOARD_ID not set in environment"):
        client.add_to_sprint_by_name(
            "AAP-test_add_to_sprint_board_id_check", "Sprint Alpha"
        )
