#!/usr/bin/env python
"""
This module contains test cases for the command-line interface (CLI) command responsible for creating issues in a
project management system, such as JIRA, using the pytest framework.

The tests validate the functionality of the `create_issue` function across various scenarios, including:
- Handling `FileNotFoundError` when template files are missing.
- Managing exceptions raised by the AI service during text improvement.
- Successful creation of an issue with proper output verification.

Each test case utilizes mocking to isolate the functionality being tested, ensuring that tests are reliable and not
dependent on external systems or files. The module includes functions to simulate different error conditions and
validate the output of the CLI commands.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from exceptions.exceptions import AiError


def test_create_file_not_found(cli):
    """
    Mock the TemplateLoader to raise FileNotFoundError when trying to load a template file.
    This function is used for testing purposes and takes a 'cli' parameter representing the command-line interface.

    Arguments:
    - cli (object): The command-line interface object to be tested.

    Exceptions:
    - FileNotFoundError: Raised when the TemplateLoader fails to load a template file.

    Side Effects:
    - Modifies the TemplateLoader to raise FileNotFoundError when attempting to load a template file.
    - Captures the exit and asserts that the correct exception is raised during the test.
    """

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
    """
    Set the template directory path for the CLI to a non-existent directory.

    Arguments:
    - cli (object): An instance of the CLI class.
    - capsys (object): Pytest fixture for capturing stdout and stderr outputs.

    Side Effects:
    - Modifies the template directory path of the CLI instance.

    Exceptions:
    - FileNotFoundError: Raised when the template file is not found.

    The function sets the template directory path of the CLI instance to a non-existent directory and then mocks the
    TemplateLoader to raise a FileNotFoundError. It creates a mock Args object, calls the cli.create_issue() method
    with Args, and asserts that the expected error message is printed.
    """

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
    """
    Handles exception raised when calling the AI service to improve text.

    Arguments:
    - cli: An object representing the CLI application.
    - capsys: A fixture provided by pytest to capture stdout and stderr.

    Exceptions:
    - AiError: Raised when the AI service fails to improve the text.

    Side Effects:
    - Modifies the behavior of the AI provider by setting the side effect of raising an AiError when improve_text is
    called.
    """

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
    """
    This function is a test function for the 'cli_create_issue' command. It mocks the behavior of the TemplateLoader
    class by using MagicMock and Patch to simulate the loading of a template with specific fields and a rendered
    description. It is used to test the functionality of creating an issue via the CLI.

    Arguments:
    - cli: An object representing the CLI interface.
    - capsys: A fixture provided by pytest to capture stdout and stderr outputs during testing.

    Side Effects:
    - Modifies the behavior of the TemplateLoader class using MagicMock and Patch to simulate specific template loading
    and rendering.
    """

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
