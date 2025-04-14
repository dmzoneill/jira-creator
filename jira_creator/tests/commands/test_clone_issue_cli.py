from unittest.mock import MagicMock


def test_clone_issue_ai_fail(cli, capsys):
    # Mock the clone_issue method
    cli.jira.clone_issue = MagicMock()

    class Args:
        issue_key = "AAP-test_clone_issue_ai_fail"

    cli.clone_issue(Args())
