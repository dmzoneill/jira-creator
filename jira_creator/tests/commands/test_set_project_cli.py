from unittest.mock import MagicMock

import pytest
from exceptions.exceptions import SetProjectError


def test_cli_set_project_success(cli, capsys):
    cli.jira.set_project = MagicMock(return_value={})

    class Args:
        issue_key = "PROJ-123"
        project_key = "NEWPROJ"

    cli.set_project(Args())

    out = capsys.readouterr().out
    assert "Project 'NEWPROJ' set for issue 'PROJ-123'" in out


def test_cli_set_project_failure(cli, capsys):
    cli.jira.set_project = MagicMock(
        side_effect=SetProjectError("Failed to set project")
    )

    class Args:
        issue_key = "PROJ-123"
        project_key = "NEWPROJ"

    with pytest.raises(SetProjectError):
        cli.set_project(Args())

    out = capsys.readouterr().out
    assert "❌ Failed to set project" in out
