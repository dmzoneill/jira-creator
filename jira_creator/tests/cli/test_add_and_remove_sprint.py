from unittest.mock import MagicMock

from jira_creator.rh_jira import JiraCLI


def test_add_sprint(monkeypatch):
    cli = JiraCLI()
    cli.jira.add_to_sprint_by_name = MagicMock()

    class Args:
        issue_key = "AAP-1"
        sprint_name = "Sprint 1"

    cli.add_sprint(Args())
    cli.jira.add_to_sprint_by_name.assert_called_once()


def test_remove_sprint(monkeypatch):
    cli = JiraCLI()
    cli.jira.remove_from_sprint = MagicMock()

    class Args:
        issue_key = "AAP-1"

    cli.remove_sprint(Args())
    cli.jira.remove_from_sprint.assert_called_once()
