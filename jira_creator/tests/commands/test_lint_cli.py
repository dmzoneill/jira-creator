from unittest.mock import MagicMock


def test_lint_command_flags_errors(cli, capsys):

    cli.ai_provider = MagicMock()
    cli.ai_provider.improve_text.side_effect = lambda prompt, text: (
        "too short" if text in ["Bad", "Meh"] else "OK"
    )

    fake_issue = {
        "fields": {
            "summary": "Bad",
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


def test_lint_command_success(cli, capsys):

    cli.ai_provider = MagicMock()
    cli.ai_provider.improve_text.side_effect = lambda prompt, text: "OK"

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
            "customfield_12311140": {
                "name": "Epic Name"
            },  # Add assigned Epic for a pass
        }
    }

    cli.jira._request.return_value = clean_issue

    class Args:
        issue_key = "AAP-321"

    cli.lint(Args())
    out = capsys.readouterr().out
    assert "✅ AAP-321 passed all lint checks" in out


def test_lint_command_exception(cli, capsys):
    # ✅ Fix: Mock ai_provider on cli directly
    cli.ai_provider = MagicMock()
    cli.ai_provider.improve_text.side_effect = lambda prompt, text: "OK"

    cli.jira._request.side_effect = Exception("Simulated fetch failure")

    class Args:
        issue_key = "AAP-404"

    cli.lint(Args())
    out = capsys.readouterr().out
    assert "❌ Failed to lint issue AAP-404: Simulated fetch failure" in out
