from unittest.mock import MagicMock

import pytest
from exceptions.exceptions import SetStatusError


def test_set_status_exception(cli, capsys):
    # Mock the set_status method to simulate an exception
    cli.jira.set_status = MagicMock(side_effect=SetStatusError("bad status"))

    class Args:
        issue_key = "AAP-test_set_status_exception"
        status = "Invalid"

    with pytest.raises(SetStatusError):
        # Call the method
        cli.set_status(Args())

    # Capture the output
    out = capsys.readouterr().out

    # Assert that the correct error message was printed
    assert "❌ Failed to update status" in out
