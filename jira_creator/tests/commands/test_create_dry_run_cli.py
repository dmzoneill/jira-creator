from unittest.mock import MagicMock, patch

import pytest
from exceptions.exceptions import CreateIssueError


def test_create_dry_run(cli):
    cli.ai_provider = MagicMock()

    # Mock method: build_payload returns a payload with summary
    cli.jira.build_payload = lambda s, d, t: {"fields": {"summary": s}}

    # Mock create_issue to just return a fake issue key
    cli.jira.create_issue = lambda payload: "AAP-test_create_dry_run"

    class Args:
        type = "story"
        summary = "Sample summary"
        edit = False
        dry_run = True

    # Mock input to avoid blocking
    with patch("builtins.input", return_value="Test"):
        cli.create_issue(Args())


def test_create_issue_with_exception(cli):
    cli.ai_provider = MagicMock()

    # Mock method: build_payload returns a payload with summary
    cli.jira.build_payload = lambda s, d, t: {"fields": {"summary": s}}

    # Mock create_issue to raise an exception
    cli.jira.create_issue = MagicMock(
        side_effect=CreateIssueError("Failed to create issue")
    )

    class Args:
        type = "story"
        summary = "Sample summary"
        edit = False
        dry_run = False

    # Mock input to avoid blocking
    with patch("builtins.input", return_value="Test"):
        # This should raise the exception
        with pytest.raises(CreateIssueError):
            cli.create_issue(Args())
