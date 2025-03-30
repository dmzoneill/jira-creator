from jira_creator.rh_jira import JiraCLI
from unittest.mock import MagicMock


class Args:
    project = None
    component = None


def test_lint_all_with_issues(capsys):
    cli = JiraCLI()
    cli.jira = MagicMock()

    # list_issues returns two issues
    cli.jira.list_issues.return_value = [
        {"key": "AAP-1"},
        {"key": "AAP-2"},
    ]

    def fake_request(method, path, **kwargs):
        if path.endswith("AAP-1"):
            return {
                "fields": {
                    "summary": "",
                    "description": None,
                    "priority": None,
                    "customfield_12310243": None,
                    "customfield_12316543": {"value": "True"},
                    "customfield_12316544": "",  # blocked but no reason
                    "status": {"name": "In Progress"},
                    "assignee": None,
                }
            }
        if path.endswith("AAP-2"):
            return {
                "fields": {
                    "summary": "Fix bug",
                    "description": "Details",
                    "priority": {"name": "High"},
                    "customfield_12310243": 3,
                    "customfield_12316543": {"value": "False"},
                    "customfield_12316544": "",
                    "status": {"name": "To Do"},
                    "assignee": {"displayName": "Dev A"},
                }
            }

    cli.jira._request = fake_request

    cli.lint_all(Args())
    out = capsys.readouterr().out

    assert "🔍 AAP-1" in out
    assert "❌ Missing summary" in out
    assert "✅ All issues passed lint checks" not in out
    assert "🔍 AAP-2" not in out


def test_lint_all_no_issues(capsys):
    cli = JiraCLI()
    cli.jira = MagicMock()

    cli.jira.list_issues.return_value = []

    cli.lint_all(Args())
    out = capsys.readouterr().out

    assert "✅ No issues assigned to you." in out


def test_lint_all_exception(capsys):
    cli = JiraCLI()
    cli.jira = MagicMock()

    cli.jira.list_issues.side_effect = Exception("Simulated failure")

    cli.lint_all(Args())
    out = capsys.readouterr().out

    assert "❌ Failed to lint issues: Simulated failure" in out


def test_lint_all_all_pass(capsys):
    cli = JiraCLI()
    cli.jira = MagicMock()

    cli.jira.list_issues.return_value = [
        {"key": "AAP-1"},
        {"key": "AAP-2"},
    ]

    def mock_request(method, path, **kwargs):
        return {
            "fields": {
                "summary": "OK",
                "description": "OK",
                "priority": {"name": "High"},
                "customfield_12310243": 5,
                "customfield_12316543": {"value": "False"},
                "customfield_12316544": "",
                "status": {"name": "To Do"},
                "assignee": {"displayName": "Someone"},
            }
        }

    cli.jira._request = mock_request

    cli.lint_all(Args())
    out = capsys.readouterr().out

    assert "✅ All issues passed lint checks!" in out
