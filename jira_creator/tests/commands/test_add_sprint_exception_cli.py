from unittest.mock import MagicMock

import pytest
from exceptions.exceptions import AddSprintError


def test_add_sprint_exception(cli, capsys):
    # Mock the add_to_sprint_by_name method to raise an exception
    cli.jira.add_to_sprint_by_name = MagicMock(side_effect=AddSprintError("fail"))

    class Args:
        issue_key = "AAP-test_add_sprint_exception"
        sprint_name = "Sprint X"

    with pytest.raises(AddSprintError):
        # Call the add_sprint method and handle the exception
        cli.add_sprint(Args())

    # Capture the output
    out = capsys.readouterr().out

    # Check that the expected failure message is present
    assert "❌" in out
