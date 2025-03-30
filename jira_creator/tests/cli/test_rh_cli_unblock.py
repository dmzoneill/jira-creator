from unittest.mock import MagicMock

from jira_creator.rh_jira import JiraCLI


def test_unblock_command_success(monkeypatch, capsys):
    cli = JiraCLI()
    cli.jira = MagicMock()

    called = {}

    def mock_unblock(issue_key):
        called["issue_key"] = issue_key

    cli.jira.unblock_issue = mock_unblock

    class Args:
        issue_key = "AAP-123"

    cli.unblock(Args())

    out = capsys.readouterr().out
    assert "✅ AAP-123 marked as unblocked" in out
    assert called["issue_key"] == "AAP-123"


def test_unblock_command_failure(monkeypatch, capsys):
    cli = JiraCLI()

    def raise_exception(issue_key):
        raise Exception("Simulated unblock failure")

    cli.jira = MagicMock()
    cli.jira.unblock_issue = raise_exception

    class Args:
        issue_key = "AAP-999"

    cli.unblock(Args())

    out = capsys.readouterr().out
    assert "❌ Failed to unblock AAP-999: Simulated unblock failure" in out
