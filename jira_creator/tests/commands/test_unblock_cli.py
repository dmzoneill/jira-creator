from unittest.mock import MagicMock


def test_unblock_command_success(cli, capsys):
    called = {}

    def mock_unblock(issue_key):
        called["issue_key"] = issue_key

    cli.jira.unblock_issue = mock_unblock

    class Args:
        issue_key = "AAP-test_unblock_command_success"

    cli.unblock(Args())

    out = capsys.readouterr().out
    assert "✅ AAP-test_unblock_command_success marked as unblocked" in out
    assert called["issue_key"] == "AAP-test_unblock_command_success"


def test_unblock_command_failure(cli, capsys):
    def raise_exception(issue_key):
        raise Exception("Simulated unblock failure")

    cli.jira = MagicMock()
    cli.jira.unblock_issue = raise_exception

    class Args:
        issue_key = "AAP-test_unblock_command_failure"

    cli.unblock(Args())

    out = capsys.readouterr().out
    assert (
        "❌ Failed to unblock AAP-test_unblock_command_failure: Simulated unblock failure"
        in out
    )
