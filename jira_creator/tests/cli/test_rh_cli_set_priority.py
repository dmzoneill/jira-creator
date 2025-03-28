from jira_creator.rh_jira import JiraCLI
from unittest.mock import MagicMock


def test_set_priority(monkeypatch):
    cli = JiraCLI()
    monkeypatch.setattr(cli.jira, "set_priority", MagicMock())

    class Args:
        issue_key = "AAP-100"
        priority = "High"

    cli.set_priority(Args())
    cli.jira.set_priority.assert_called_once_with("AAP-100", "High")
