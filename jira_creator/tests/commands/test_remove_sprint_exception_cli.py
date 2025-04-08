from unittest.mock import MagicMock

import pytest
from exceptions.exceptions import RemoveFromSprintError


def test_remove_sprint_error(cli, capsys):
    # Mock the remove_from_sprint method to raise an exception
    cli.jira.remove_from_sprint = MagicMock(side_effect=RemoveFromSprintError("fail"))

    class Args:
        issue_key = "AAP-test_remove_sprint_error"

    with pytest.raises(RemoveFromSprintError):
        # Call the remove_sprint method
        cli.remove_sprint(Args())

    # Capture the output and assert the error message
    out = capsys.readouterr().out
    assert "❌ Failed to remove sprint" in out
