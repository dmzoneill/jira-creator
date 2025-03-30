from jira.client import JiraClient
from unittest.mock import MagicMock
import pytest


def test_add_to_sprint_board_id_missing():
    # Mock the environment variable access or JiraClient constructor behavior
    with pytest.raises(EnvironmentError, match="JIRA_BOARD_ID not set in environment"):
        # Mock the JIRA client constructor and its behavior
        with MagicMock() as mock_client:
            # Simulate missing or invalid board_id
            mock_client.board_id = None

            # When JiraClient is instantiated, it should raise EnvironmentError
            JiraClient()
