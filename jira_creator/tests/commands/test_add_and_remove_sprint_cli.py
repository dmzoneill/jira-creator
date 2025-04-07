from unittest.mock import MagicMock


def test_add_sprint(cli):
    cli.jira.add_to_sprint_by_name = MagicMock()

    class Args:
        issue_key = "AAP-test_add_sprint"
        sprint_name = "Sprint 1"

    cli.add_sprint(Args())
    cli.jira.add_to_sprint_by_name.assert_called_once()


def test_remove_sprint(cli):
    cli.jira.remove_from_sprint = MagicMock()

    class Args:
        issue_key = "AAP-test_remove_sprint"

    cli.remove_sprint(Args())
    cli.jira.remove_from_sprint.assert_called_once()
