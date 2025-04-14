from unittest.mock import MagicMock

import pytest


def test_list_sprints(cli, capsys):
    # Mock the list_sprints method
    response = MagicMock()
    cli.jira.list_sprints = MagicMock(return_value=["Sprint 1", "Sprint 2"])

    class Args:
        board_id = "dummy_issue_key"  # Not used in the method

    response = cli.list_sprints(Args())

    # Capture output and assert
    out = capsys.readouterr().out
    assert "Sprint 1" in out
    assert "Sprint 2" in out
    assert response == ["Sprint 1", "Sprint 2"]


def test_list_sprints_exception(cli, capsys):
    # Mock the list_sprints method
    cli.jira.list_sprints = MagicMock(side_effect=Exception("Failed"))

    class Args:
        board_id = "dummy_issue_key"  # Not used in the method

    with pytest.raises(Exception):
        cli.list_sprints(Args())
