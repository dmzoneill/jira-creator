from unittest.mock import MagicMock

from jira_creator.rh_jira import JiraCLI


def test_lint_command_flags_errors(capsys):
    cli = JiraCLI()
    cli.jira = MagicMock()

    # ✅ Mock ai_provider
    cli.jira.ai_provider = MagicMock()
    cli.jira.ai_provider.improve_text.side_effect = lambda prompt, text: (
        "too short" if text in ["Bad", "Meh"] else "OK"
    )

    fake_issue = {
        "fields": {
            "summary": "Bad",  # Not empty to trigger AI logic
            "description": "Meh",
            "priority": None,
            "customfield_12310243": None,
            "customfield_12316543": {"value": "True"},
            "customfield_12316544": "",
            "status": {"name": "In Progress"},
            "assignee": None,
        }
    }

    cli.jira._request.return_value = fake_issue

    class Args:
        issue_key = "AAP-999"

    cli.lint(Args())
    out = capsys.readouterr().out

    assert "⚠️ Lint issues found in AAP-999" in out
    assert "❌ Summary: too short" in out
    assert "❌ Description: too short" in out
    assert "❌ Priority not set" in out
    assert "❌ Story points not assigned" in out
    assert "❌ Issue is blocked but has no blocked reason" in out
    assert "❌ Issue is In Progress but unassigned" in out


def test_lint_command_success(capsys):
    cli = JiraCLI()
    cli.jira = MagicMock()

    # ✅ Add ai_provider mock
    cli.jira.ai_provider = MagicMock()
    cli.jira.ai_provider.improve_text.side_effect = lambda prompt, text: "OK"

    clean_issue = {
        "fields": {
            "summary": "Valid summary",
            "description": "All good",
            "priority": {"name": "Medium"},
            "customfield_12310243": 5,
            "customfield_12316543": {"value": "False"},
            "customfield_12316544": "",
            "status": {"name": "To Do"},
            "assignee": {"displayName": "dev"},
        }
    }

    cli.jira._request.return_value = clean_issue

    class Args:
        issue_key = "AAP-321"

    cli.lint(Args())
    out = capsys.readouterr().out
    assert "✅ AAP-321 passed all lint checks" in out


def test_lint_command_exception(capsys):
    cli = JiraCLI()
    cli.jira = MagicMock()

    # ✅ Add ai_provider mock
    cli.jira.ai_provider = MagicMock()
    cli.jira.ai_provider.improve_text.side_effect = lambda prompt, text: "OK"

    cli.jira._request.side_effect = Exception("Simulated fetch failure")

    class Args:
        issue_key = "AAP-404"

    cli.lint(Args())
    out = capsys.readouterr().out
    assert "❌ Failed to lint issue AAP-404: Simulated fetch failure" in out
