from unittest.mock import MagicMock

import pytest


def test_remove_flag(cli, capsys):
    # Mock the remove_flag method
    cli.jira.remove_flag = MagicMock(return_value={"status": "success"})

    class Args:
        issue_key = "AAP-test_remove_flag"

    response = cli.remove_flag(Args())

    # Capture output and assert
    out = capsys.readouterr().out
    assert "Removed" in out
    assert response == {"status": "success"}


def test_remove_flag_exception(cli, capsys):
    # Mock the list_sprints method
    cli.jira.remove_flag = MagicMock(side_effect=Exception("Failed"))

    class Args:
        issue_key = "dummy_issue_key"

    with pytest.raises(Exception):
        cli.remove_flag(Args())
