from unittest.mock import MagicMock


def test_set_summary_ai_fail(cli, capsys):
    cli.jira.set_summary = MagicMock()

    class Args:
        issue_key = "AAP-test_set_summary_ai_fail"
        summary = "New Summary"

    cli.set_summary(Args())
