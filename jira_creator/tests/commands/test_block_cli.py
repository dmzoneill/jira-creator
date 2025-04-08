import pytest
from exceptions.exceptions import BlockError


def test_block_command(cli, capsys):
    called = {}

    def mock_block_issue(issue_key, reason):
        called["issue_key"] = issue_key
        called["reason"] = reason

    cli.jira.block_issue = mock_block_issue

    class Args:
        issue_key = "AAP-test_block_command"
        reason = "Blocked by external dependency"

    cli.block(Args())

    captured = capsys.readouterr()
    assert "✅ AAP-test_block_command marked as blocked" in captured.out
    assert called == {
        "issue_key": "AAP-test_block_command",
        "reason": "Blocked by external dependency",
    }


def test_block_command_exception(cli, capsys):
    def mock_block_issue(issue_key, reason):
        raise BlockError("Simulated failure")

    cli.jira.block_issue = mock_block_issue

    class Args:
        issue_key = "AAP-test_block_command_exception"
        reason = "Something went wrong"

    with pytest.raises(BlockError):
        cli.block(Args())

    captured = capsys.readouterr()
    assert (
        "❌ Failed to mark AAP-test_block_command_exception as blocked: Simulated failure"
        in captured.out
    )
