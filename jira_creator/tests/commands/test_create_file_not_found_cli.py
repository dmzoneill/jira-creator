from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from jira_creator.rh_jira import JiraCLI


def test_create_file_not_found():
    cli = JiraCLI()

    # Mock the TemplateLoader to raise FileNotFoundError
    template_loader_mock = MagicMock(side_effect=FileNotFoundError("missing.tmpl"))
    cli.template_loader = template_loader_mock

    # Define the arguments for the CLI command
    class Args:
        type = "nonexistent"
        summary = "test"
        edit = False
        dry_run = False

    # Capture the exit and assert it raises the correct exception
    with pytest.raises(SystemExit):
        cli.create_issue(Args())


def test_create_file_not_found_error(capsys):
    cli = JiraCLI()
    cli.template_dir = Path("non_existent_directory")

    # Mock TemplateLoader to raise a FileNotFoundError
    with patch("commands.create_issue.TemplateLoader") as MockTemplateLoader:
        MockTemplateLoader.side_effect = FileNotFoundError("Template file not found")

        # Create mock Args object
        class Args:
            type = "story"
            edit = False
            dry_run = False
            summary = "Test summary"

        # Capture the SystemExit exception
        with pytest.raises(SystemExit):
            cli.create_issue(Args)

        # Capture the printed output
        captured = capsys.readouterr()
        assert "Error: Template file not found" in captured.out


def test_create_ai_exception_handling(capsys):
    cli = JiraCLI()

    cli.ai_provider = MagicMock()
    cli.ai_provider.improve_text.side_effect = Exception("AI service failed")

    with patch("commands.create_issue.TemplateLoader") as MockTemplateLoader:
        mock_template = MagicMock()
        mock_template.get_fields.return_value = ["field1", "field2"]
        mock_template.render_description.return_value = "Mocked description"
        MockTemplateLoader.return_value = mock_template

        with patch("builtins.input", return_value="test_input"):
            with patch("subprocess.call") as _:
                with (
                    patch("commands.create_issue.JiraIssueType") as MockJiraIssueType,
                    patch(
                        "commands.create_issue.JiraPromptLibrary.get_prompt"
                    ) as MockGetPrompt,
                ):
                    MockJiraIssueType.return_value = MagicMock()
                    MockGetPrompt.return_value = "Mocked prompt"

                    cli.jira = MagicMock()
                    cli.jira.build_payload.return_value = {
                        "summary": "Mock summary",
                        "description": "Mock description",
                    }
                    cli.jira.create_issue.return_value = "AAP-123"

                    class Args:
                        type = "story"
                        edit = False
                        dry_run = False
                        summary = "Test summary"

                    cli.create_issue(Args)

                captured = capsys.readouterr()
                assert (
                    "⚠️ AI cleanup failed. Using original text. Error: AI service failed"
                    in captured.out
                )


def test_create(capsys):
    cli = JiraCLI()

    with patch("commands.create_issue.TemplateLoader") as MockTemplateLoader:
        mock_template = MagicMock()
        mock_template.get_fields.return_value = ["field1", "field2"]
        mock_template.render_description.return_value = "Mocked description"
        MockTemplateLoader.return_value = mock_template

        with patch("builtins.input", return_value="test_input"):
            with (
                patch("commands.create_issue.JiraIssueType") as MockJiraIssueType,
                patch(
                    "commands.create_issue.JiraPromptLibrary.get_prompt"
                ) as MockGetPrompt,
            ):
                MockJiraIssueType.return_value = MagicMock()
                MockGetPrompt.return_value = "Mocked prompt"

                cli.ai_provider = MagicMock()
                cli.ai_provider.improve_text.return_value = "Mocked improved text"

                cli.jira = MagicMock()
                cli.jira.build_payload.return_value = {
                    "summary": "Mock summary",
                    "description": "Mock description",
                }
                cli.jira.create_issue.return_value = "AAP-123"
                cli.jira.jira_url = "https://jira.example.com"

                class Args:
                    type = "story"
                    edit = False
                    dry_run = False
                    summary = "Test summary"

                with patch("subprocess.call") as _:
                    cli.create_issue(Args)

                captured = capsys.readouterr()
                assert (
                    "✅ Created: https://jira.example.com/browse/AAP-123"
                    in captured.out
                )
