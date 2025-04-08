from unittest.mock import MagicMock

import pytest
from exceptions.exceptions import MigrateError


def test_migrate_to_exception(cli, capsys):
    # Mock the migrate_issue method to raise an exception
    cli.jira.migrate_issue = MagicMock(side_effect=MigrateError("fail"))
    cli.jira.jira_url = "http://fake"

    # Mock the Args class with necessary attributes
    class Args:
        issue_key = "AAP-test_migrate_to_exception"
        new_type = "story"

    with pytest.raises(MigrateError):
        # Call the migrate method
        cli.migrate(Args())

    # Capture the output and assert the error message
    out = capsys.readouterr().out
    assert "❌ Migration failed" in out
