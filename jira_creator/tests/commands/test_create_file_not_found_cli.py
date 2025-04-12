from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from exceptions.exceptions import AiError


def test_create_file_not_found(cli):
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
    with pytest.raises(FileNotFoundError):
        cli.create_issue(Args())


def test_create_file_not_found_error(cli, capsys):
    cli.template_dir = Path("non_existent_directory")

    # Mock TemplateLoader to raise a FileNotFoundError
    with patch("commands.cli_create_issue.TemplateLoader") as MockTemplateLoader:
        MockTemplateLoader.side_effect = FileNotFoundError("Template file not found")

        # Create mock Args object
        class Args:
            type = "story"
            edit = False
            dry_run = False
            summary = "Test summary"

        # Capture the SystemExit exception
        with pytest.raises(FileNotFoundError):
            cli.create_issue(Args)

        # Capture the printed output
        captured = capsys.readouterr()
        assert "Error: Template file not found" in captured.out


def test_create_ai_exception_handling(cli, capsys):
    cli.ai_provider = MagicMock()
    cli.ai_provider.improve_text.side_effect = AiError("AI service failed")

    with patch("commands.cli_create_issue.TemplateLoader") as MockTemplateLoader:
        mock_template = MagicMock()
        mock_template.get_fields.return_value = ["field1", "field2"]
        mock_template.render_description.return_value = "Mocked description"
        MockTemplateLoader.return_value = mock_template

        with patch("builtins.input", return_value="test_input"):
            with patch("subprocess.call") as _:
                with (
                    patch("commands.cli_create_issue.IssueType") as MockIssueType,
                    patch(
                        "commands.cli_create_issue.PromptLibrary.get_prompt"
                    ) as MockGetPrompt,
                ):
                    MockIssueType.return_value = MagicMock()
                    MockGetPrompt.return_value = "Mocked prompt"

                    cli.jira = MagicMock()
                    cli.jira.build_payload.return_value = {
                        "summary": "Mock summary",
                        "description": "Mock description",
                    }
                    cli.jira.create_issue.return_value = (
                        "AAP-test_create_ai_exception_handling-0"
                    )

                    class Args:
                        type = "story"
                        edit = False
                        dry_run = False
                        summary = "Test summary"

                    with pytest.raises(AiError):
                        cli.create_issue(Args)

                    captured = capsys.readouterr()
                    assert (
                        "⚠️ AI cleanup failed. Using original text. Error: AI service failed"
                        in captured.out
                    )


def test_create(cli, capsys):
    with patch("commands.cli_create_issue.TemplateLoader") as MockTemplateLoader:
        mock_template = MagicMock()
        mock_template.get_fields.return_value = ["field1", "field2"]
        mock_template.render_description.return_value = "Mocked description"
        MockTemplateLoader.return_value = mock_template

        with patch("builtins.input", return_value="test_input"):
            with (
                patch("commands.cli_create_issue.IssueType") as MockIssueType,
                patch(
                    "commands.cli_create_issue.PromptLibrary.get_prompt"
                ) as MockGetPrompt,
            ):
                MockIssueType.return_value = MagicMock()
                MockGetPrompt.return_value = "Mocked prompt"

                cli.ai_provider = MagicMock()
                cli.ai_provider.improve_text.return_value = "Mocked improved text"

                cli.jira = MagicMock()
                cli.jira.build_payload.return_value = {
                    "summary": "Mock summary",
                    "description": "Mock description",
                }
                cli.jira.create_issue.return_value = (
                    "AAP-test_create_ai_exception_handling-1"
                )
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
                    "https://jira.example.com/browse/AAP-test_create_ai_exception_handling"
                    in captured.out
                )
