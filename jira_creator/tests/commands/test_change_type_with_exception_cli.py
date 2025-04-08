from unittest.mock import MagicMock

import pytest
from exceptions.exceptions import ChangeTypeError


def test_change_type_failure(cli, capsys):
    # Mocking the change_issue_type method to raise an exception
    cli.jira.change_issue_type = MagicMock(side_effect=ChangeTypeError("Boom"))

    class Args:
        issue_key = "AAP-test_change_type_failure"
        new_type = "task"

    with pytest.raises(ChangeTypeError):
        # Call the method
        cli.change_type(Args())

    # Capture the output
    out = capsys.readouterr().out
    assert "❌ Error" in out
    assert "Boom" in out  # Optionally check that the exception message is included
