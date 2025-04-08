from unittest.mock import MagicMock

import pytest
from core.env_fetcher import EnvFetcher
from exceptions.exceptions import LintError


def test_lint_command_flags_errors(mock_save_cache, cli, capsys):
    cli.ai_provider = MagicMock()
    cli.ai_provider.improve_text.side_effect = lambda prompt, text: (
        "too short" if text in ["Bad", "Meh"] else "OK"
    )

    fake_issue = {
        "fields": {
            "summary": "Bad",
            "description": "Meh",
            "priority": None,
            EnvFetcher.get("JIRA_STORY_POINTS_FIELD"): None,
            EnvFetcher.get("JIRA_BLOCKED_FIELD"): {"value": "True"},
            EnvFetcher.get("JIRA_BLOCKED_REASON_FIELD"): "",
            "status": {"name": "In Progress"},
            "assignee": None,
        }
    }

    cli.jira._request.return_value = fake_issue

    class Args:
        issue_key = "AAP-test_lint_command_flags_errors"

    cli.lint(Args())
    out = capsys.readouterr().out

    assert "⚠️ Lint issues found in AAP-test_lint_command_flags_errors" in out
    assert "❌ Summary: too short" in out
    assert "❌ Description: too short" in out
    assert "❌ Priority not set" in out
    assert "❌ Story points not assigned" in out
    assert "❌ Issue is blocked but has no blocked reason" in out
    assert "❌ Issue is In Progress but unassigned" in out


def test_lint_command_success(mock_save_cache, cli, capsys):
    cli.ai_provider = MagicMock()
    cli.ai_provider.improve_text.side_effect = lambda prompt, text: "OK"

    clean_issue = {
        "fields": {
            "summary": "Valid summary",
            "description": "All good",
            "priority": {"name": "Medium"},
            EnvFetcher.get("JIRA_STORY_POINTS_FIELD"): 5,
            EnvFetcher.get("JIRA_BLOCKED_FIELD"): {"value": "False"},
            EnvFetcher.get("JIRA_BLOCKED_REASON_FIELD"): "",
            "status": {"name": "To Do"},
            "assignee": {"displayName": "dev"},
            EnvFetcher.get("JIRA_EPIC_FIELD"): {
                "name": "Epic Name"
            },  # Add assigned Epic for a pass
        }
    }

    cli.jira._request.return_value = clean_issue

    class Args:
        issue_key = "AAP-test_lint_command_success"

    cli.lint(Args())
    out = capsys.readouterr().out
    assert "✅ AAP-test_lint_command_success passed all lint checks" in out


def test_lint_command_exception(mock_save_cache, cli, capsys):
    # ✅ Fix: Mock ai_provider on cli directly
    cli.ai_provider = MagicMock()
    cli.ai_provider.improve_text.side_effect = lambda prompt, text: "OK"
    cli.jira._request.side_effect = LintError("Simulated fetch failure")

    class Args:
        issue_key = "AAP-test_lint_command_exception"

    with pytest.raises(LintError):
        cli.lint(Args())

    out = capsys.readouterr().out
    assert (
        "❌ Failed to lint issue AAP-test_lint_command_exception: Simulated fetch failure"
        in out
    )
