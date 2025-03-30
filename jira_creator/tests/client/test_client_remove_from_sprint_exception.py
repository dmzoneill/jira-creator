from unittest.mock import MagicMock

from jira.client import JiraClient


def test_remove_from_sprint_error(capsys):
    client = JiraClient()

    # Mock the _request method to raise an exception
    client._request = MagicMock(side_effect=Exception("fail"))

    # Call the remove_from_sprint method
    client.remove_from_sprint("AAP-1")

    # Capture the output and assert the error message
    out = capsys.readouterr().out
    assert "❌ Failed to remove from sprint" in out
