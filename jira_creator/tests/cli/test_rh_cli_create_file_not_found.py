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
        cli.create(Args())


def test_create_file_not_found_error(capsys):
    cli = JiraCLI()
    cli.template_dir = "non_existent_directory"  # Simulate missing template directory

    # Mock TemplateLoader to raise a FileNotFoundError
    with patch("jira_creator.rh_jira.TemplateLoader") as MockTemplateLoader:
        MockTemplateLoader.side_effect = FileNotFoundError("Template file not found")

        # Create mock Args object
        class Args:
            type = "story"
            edit = False
            dry_run = False
            summary = "Test summary"

        # Capture the SystemExit exception
        with pytest.raises(SystemExit):
            cli.create(Args)

        # Capture the printed output
        captured = capsys.readouterr()

        # Assert that the error message is printed correctly
        assert "Error: Template file not found" in captured.out


def test_create_ai_exception_handling(capsys):
    cli = JiraCLI()

    # Mock AI provider
    cli.ai_provider = MagicMock()
    cli.ai_provider.improve_text.side_effect = Exception("AI service failed")

    # Mock TemplateLoader to avoid file access and slow processing
    with patch("jira_creator.rh_jira.TemplateLoader") as MockTemplateLoader:
        mock_template = MagicMock()
        mock_template.get_fields.return_value = ["field1", "field2"]  # Mock fields
        mock_template.render_description.return_value = "Mocked description"
        MockTemplateLoader.return_value = mock_template

        # Mock input function to avoid blocking the test
        with patch("builtins.input", return_value="test_input"):
            # Mock subprocess.call to avoid external editor
            with patch("subprocess.call") as _:
                # Mock JiraIssueType and get_prompt methods to avoid slow processing
                with (
                    patch("jira_creator.rh_jira.JiraIssueType") as MockJiraIssueType,
                    patch(
                        "jira_creator.rh_jira.JiraPromptLibrary.get_prompt"
                    ) as MockGetPrompt,
                ):
                    MockJiraIssueType.return_value = MagicMock()
                    MockGetPrompt.return_value = "Mocked prompt"

                    # Mock the Jira build_payload and create_issue methods to avoid API calls
                    cli.jira = MagicMock()
                    cli.jira.build_payload.return_value = {
                        "summary": "Mock summary",
                        "description": "Mock description",
                    }
                    cli.jira.create_issue.return_value = "AAP-123"

                    # Create mock Args object
                    class Args:
                        type = "story"
                        edit = False
                        dry_run = False
                        summary = "Test summary"

                    # Run the create method with mocked AI failure
                    cli.create(Args)

                # Capture the printed output
                captured = capsys.readouterr()

                # Assert the AI error message is printed
                assert (
                    "⚠️ AI cleanup failed. Using original text. Error: AI service failed"
                    in captured.out
                )


def test_create(capsys):
    cli = JiraCLI()

    # Mock TemplateLoader to avoid file access and slow processing
    with patch("jira_creator.rh_jira.TemplateLoader") as MockTemplateLoader:
        mock_template = MagicMock()
        mock_template.get_fields.return_value = ["field1", "field2"]  # Mock fields
        mock_template.render_description.return_value = "Mocked description"
        MockTemplateLoader.return_value = mock_template

        # Mock the input function to avoid blocking the test
        with patch("builtins.input", return_value="test_input"):
            # Mock JiraIssueType and get_prompt methods to avoid slow processing
            with (
                patch("jira_creator.rh_jira.JiraIssueType") as MockJiraIssueType,
                patch(
                    "jira_creator.rh_jira.JiraPromptLibrary.get_prompt"
                ) as MockGetPrompt,
            ):
                MockJiraIssueType.return_value = MagicMock()
                MockGetPrompt.return_value = "Mocked prompt"

                # Mock the AI provider to avoid external calls
                cli.ai_provider = MagicMock()
                cli.ai_provider.improve_text.return_value = "Mocked improved text"

                # Mock the Jira build_payload and create_issue methods to avoid API calls
                cli.jira = MagicMock()
                cli.jira.build_payload.return_value = {
                    "summary": "Mock summary",
                    "description": "Mock description",
                }
                cli.jira.create_issue.return_value = "AAP-123"

                # Mock the jira_url to return a valid URL string
                cli.jira.jira_url = "https://jira.example.com"

                # Create mock Args object
                class Args:
                    type = "story"
                    edit = False
                    dry_run = False
                    summary = "Test summary"

                # Mock subprocess.call to avoid opening external editors
                with patch("subprocess.call") as _:
                    cli.create(Args)

                # Capture the printed output
                captured = capsys.readouterr()

                # Assert the correct messages were printed
                assert (
                    "✅ Created: https://jira.example.com/browse/AAP-123"
                    in captured.out
                )
