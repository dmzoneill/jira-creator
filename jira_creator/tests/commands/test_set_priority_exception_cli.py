from unittest.mock import MagicMock

import pytest
from exceptions.exceptions import SetPriorityError


def test_set_priority_error(cli, capsys):
    # Mock the set_priority method to simulate an exception
    cli.jira.set_priority = MagicMock(side_effect=SetPriorityError("fail"))

    class Args:
        issue_key = "AAP-test_set_priority_error"
        priority = "High"

    with pytest.raises(SetPriorityError):
        # Call the method
        cli.set_priority(Args())

    # Capture the output
    out = capsys.readouterr().out

    # Assert that the correct error message was printed
    assert "❌ Failed to set priority" in out
