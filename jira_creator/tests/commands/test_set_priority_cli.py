from unittest.mock import MagicMock


def test_set_priority(cli):
    cli.jira = MagicMock()

    class Args:
        issue_key = "AAP-test_set_priority"
        priority = "High"

    cli.set_priority(Args())

    cli.jira.set_priority.assert_called_once_with("AAP-test_set_priority", "High")
