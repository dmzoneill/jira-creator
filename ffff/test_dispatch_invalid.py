from jira_creator.rh_jira import JiraCLI
from unittest.mock import MagicMock


def test_dispatch_command_invalid(capsys):
    cli = JiraCLI()

    # Mock _dispatch_command to simulate a failed command
    cli._dispatch_command = MagicMock(side_effect=Exception("Command failed"))

    class Args:
        command = "nonexistent"

    try:
        cli._dispatch_command(Args())
    except Exception as e:
        out = capsys.readouterr().out
        assert "❌ Command failed" in out
