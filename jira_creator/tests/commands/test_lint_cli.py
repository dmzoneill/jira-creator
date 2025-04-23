"""
This file contains unit tests for the lint command flags errors, success, and exceptions in the CLI application.

The tests include scenarios where lint issues are found, all lint checks pass successfully, and an exception is raised
during linting.

The tests utilize the pytest framework and mock objects for testing. The tests cover various scenarios such as checking
issue fields, improving text, handling exceptions, and verifying the output messages.

The test_lint_command_flags_errors function checks for lint issues in a fake JIRA issue with specific field values and
asserts the expected error messages.

The test_lint_command_success function tests a clean JIRA issue with all fields properly set, ensuring the lint check
passes successfully.

The test_lint_command_exception function simulates a fetch failure by raising a LintError during linting and verifies
the appropriate error message is displayed.

Please ensure all dependencies are properly installed before running these tests.
"""

from unittest.mock import MagicMock

import pytest
from core.env_fetcher import EnvFetcher
from exceptions.exceptions import LintError


def test_lint_command_flags_errors(mock_save_cache, cli, capsys):
    """
    Simulate linting command flags and handle errors.

    Arguments:
    - mock_save_cache: A mock object for saving cache.
    - cli: An object representing the command-line interface.
    - capsys: A fixture for capturing stdout and stderr outputs.

    Side Effects:
    - Modifies the 'ai_provider' attribute of the 'cli' object to a MagicMock object.
    - Sets up a side effect for the 'improve_text' method of 'ai_provider' to return "too short" for texts "Bad" and
    "Meh", and "OK" for other texts.
    """

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
    """
    Execute a test for the successful execution of a lint command.

    Arguments:
    - mock_save_cache: An object used for mocking cache saving.
    - cli: An object representing the command-line interface.
    - capsys: A fixture provided by pytest to capture stdout and stderr.

    Side Effects:
    - Sets the 'ai_provider' attribute of the 'cli' object to a MagicMock object.
    - Configures the 'improve_text' method of the 'ai_provider' object to return "OK" for any prompt and text inputs.
    """

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
    """
    Mock and test the lint command exception handling.

    Arguments:
    - mock_save_cache: MagicMock object for saving cache.
    - cli: Command Line Interface object.
    - capsys: Pytest built-in fixture for capturing stdout and stderr.

    Exceptions:
    - LintError: Raised when a simulated fetch failure occurs during the lint command execution.
    """

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
