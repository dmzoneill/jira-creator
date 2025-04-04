from unittest.mock import MagicMock, patch  # Add patch here

from jira_creator.rh_jira import JiraCLI


def test_create_dry_run():
    cli = JiraCLI()
    cli.jira = MagicMock()
    cli.ai_provider = MagicMock()

    # Mock method: build_payload returns a payload with summary
    cli.jira.build_payload = lambda s, d, t: {"fields": {"summary": s}}

    # Mock create_issue to just return a fake issue key
    cli.jira.create_issue = lambda payload: "AAP-123"

    class Args:
        type = "story"
        summary = "Sample summary"
        edit = False
        dry_run = True

    # Mock input to avoid blocking
    with patch("builtins.input", return_value="Test"):
        cli.create_issue(Args())


def test_create_issue_with_exception():
    cli = JiraCLI()
    cli.jira = MagicMock()
    cli.ai_provider = MagicMock()

    # Mock method: build_payload returns a payload with summary
    cli.jira.build_payload = lambda s, d, t: {"fields": {"summary": s}}

    # Mock create_issue to raise an exception
    cli.jira.create_issue = MagicMock(side_effect=Exception("Failed to create issue"))

    class Args:
        type = "story"
        summary = "Sample summary"
        edit = False
        dry_run = False

    # Mock input to avoid blocking
    with patch("builtins.input", return_value="Test"):
        # This should raise the exception
        cli.create_issue(Args())
