from unittest.mock import MagicMock, patch

import pytest

from jira_creator.jira import jira_prompts
from jira_creator.rh_jira import JiraCLI


def test_create_value_error_prompt():
    cli = JiraCLI()

    # Mock create_issue to return a fake issue key
    cli.jira.create_issue = MagicMock(return_value="AAP-123")

    # Mock the improve_text method to return the text unchanged
    cli.ai_provider.improve_text = MagicMock(side_effect=lambda p, t: t)

    # Mock TemplateLoader to return a DummyTemplate instance
    class DummyTemplate:
        pass

    cli.jira.TemplateLoader = MagicMock(return_value=DummyTemplate())

    # Simulate unknown issue type causing ValueError in the JiraIssueType method
    jira_prompts.JiraIssueType = MagicMock(side_effect=ValueError("unknown type"))

    # Create a dummy Args class to simulate the input
    class Args:
        type = "unknown"
        summary = "Some summary"
        edit = False
        dry_run = True

    # Catch the SystemExit triggered by sys.exit(1) when FileNotFoundError occurs
    with pytest.raises(SystemExit) as excinfo:
        cli.create_issue(Args())

    # Assert that sys.exit(1) was called
    assert excinfo.value.code == 1


@patch("commands.create_issue.TemplateLoader")
def test_create_value_error_prompt_fallback(MockTemplateLoader, capsys):
    mock_template = MagicMock()
    mock_template.get_fields.return_value = []
    mock_template.render_description.return_value = "desc"
    MockTemplateLoader.return_value = mock_template

    cli = JiraCLI()
    cli.ai_provider = MagicMock()
    cli.ai_provider.improve_text.return_value = "desc"
    cli.jira = MagicMock()
    cli.jira.build_payload.return_value = {"summary": "s", "description": "desc"}
    cli.jira.create_issue.return_value = "FOO-123"
    cli.jira.jira_url = "http://example.com"

    with patch(
        "commands.create_issue.JiraIssueType", side_effect=ValueError("bad type")
    ):
        with patch(
            "commands.create_issue.JiraPromptLibrary.get_prompt",
            return_value="fallback",
        ):

            class Args:
                type = "invalidtype"
                summary = "s"
                edit = False
                dry_run = False

            cli.create_issue(Args)
            out = capsys.readouterr().out
            assert "⚠️ Unknown issue type 'invalidtype'. Using default prompt." in out


@patch("commands.create_issue.TemplateLoader")
def test_create_issue_failure(MockTemplateLoader, capsys):
    mock_template = MagicMock()
    mock_template.get_fields.return_value = []
    mock_template.render_description.return_value = "desc"
    MockTemplateLoader.return_value = mock_template

    cli = JiraCLI()
    cli.ai_provider = MagicMock()
    cli.ai_provider.improve_text.return_value = "desc"
    cli.jira = MagicMock()
    cli.jira.build_payload.return_value = {"summary": "s", "description": "desc"}
    cli.jira.create_issue.side_effect = Exception("API failed")

    class Args:
        type = "story"
        summary = "s"
        edit = False
        dry_run = False

    cli.create_issue(Args)
    out = capsys.readouterr().out
    assert "❌ Failed to create issue: API failed" in out
