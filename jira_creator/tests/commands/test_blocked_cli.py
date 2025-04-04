from unittest.mock import MagicMock

from jira_creator.rh_jira import JiraCLI


class Args:
    project = None
    component = None
    user = None


def test_blocked_issues_found(capsys):
    cli = JiraCLI()
    cli.jira = MagicMock()

    cli.jira.list_issues.return_value = [
        {
            "key": "AAP-123",
            "fields": {
                "status": {"name": "In Progress"},
                "assignee": {"displayName": "Jane"},
                "customfield_12316543": {"value": "True"},
                "customfield_12316544": "Waiting for DB",
                "summary": "Fix DB timeout issue",
            },
        },
        {
            "key": "AAP-456",
            "fields": {
                "status": {"name": "Ready"},
                "assignee": {"displayName": "John"},
                "customfield_12316543": {"value": "False"},
                "customfield_12316544": "",
                "summary": "Update readme",
            },
        },
    ]

    cli.blocked(Args())

    out = capsys.readouterr().out
    assert "🔒 Blocked issues:" in out
    assert "AAP-123" in out
    assert "Waiting for DB" in out
    assert "AAP-456" not in out


def test_blocked_no_issues(capsys):
    cli = JiraCLI()
    cli.jira = MagicMock()
    cli.jira.list_issues.return_value = []

    cli.blocked(Args())

    out = capsys.readouterr().out
    assert "✅ No issues found." in out


def test_blocked_none_blocked(capsys):
    cli = JiraCLI()
    cli.jira = MagicMock()
    cli.jira.list_issues.return_value = [
        {
            "key": "AAP-789",
            "fields": {
                "summary": "Add tests",
                "status": {"name": "To Do"},
                "assignee": {"displayName": "Alex"},
                "customfield_12316543": {"value": "False"},
                "customfield_12316544": "",
            },
        }
    ]

    cli.blocked(Args())
    out = capsys.readouterr().out
    assert "✅ No blocked issues found." in out
    assert "AAP-789" not in out


def test_blocked_exception(capsys):
    cli = JiraCLI()
    cli.jira = MagicMock()
    cli.jira.list_issues.side_effect = Exception("Boom!")

    cli.blocked(Args())

    out = capsys.readouterr().out
    assert "❌ Failed to list blocked issues: Boom!" in out
