#!/usr/bin/env python
"""Tests for the create issue plugin."""

from argparse import ArgumentParser, Namespace
from unittest.mock import Mock, patch

import pytest

from jira_creator.exceptions.exceptions import AiError, CreateIssueError
from jira_creator.plugins.create_issue_plugin import CreateIssuePlugin


class TestCreateIssuePlugin:
    """Test cases for CreateIssuePlugin."""

    def test_plugin_properties(self):
        """Test plugin properties are set correctly."""
        plugin = CreateIssuePlugin()
        assert plugin.command_name == "create-issue"
        assert plugin.help_text == "Create a new Jira issue using templates"

    def test_register_arguments(self):
        """Test argument registration."""
        plugin = CreateIssuePlugin()
        mock_parser = Mock(spec=ArgumentParser)

        plugin.register_arguments(mock_parser)

        # Check all arguments are registered
        expected_calls = [
            (
                ("type",),
                {
                    "choices": ["bug", "story", "epic", "task"],
                    "help": "Type of issue to create",
                },
            ),
            (("summary",), {"help": "Issue summary/title"}),
            (
                ("-e", "--edit"),
                {
                    "action": "store_true",
                    "help": "Open editor to modify the description before submission",
                },
            ),
            (
                ("--dry-run",),
                {
                    "action": "store_true",
                    "help": "Preview the issue without creating it",
                },
            ),
            (
                ("--no-ai",),
                {"action": "store_true", "help": "Skip AI text improvement"},
            ),
        ]

        assert mock_parser.add_argument.call_count == len(expected_calls)

    def test_rest_operation(self):
        """Test the REST operation directly."""
        plugin = CreateIssuePlugin()
        mock_client = Mock()
        mock_response = {"key": "TEST-123", "id": "10001"}
        mock_client.request.return_value = mock_response

        payload = {
            "fields": {
                "project": {"key": "TEST"},
                "summary": "Test Issue",
                "description": "Test Description",
                "issuetype": {"name": "Story"},
            }
        }

        result = plugin.rest_operation(mock_client, payload=payload)

        mock_client.request.assert_called_once_with("POST", "/rest/api/2/issue/", json_data=payload)
        assert result == mock_response

    @patch("jira_creator.plugins.create_issue_plugin.TemplateLoader")
    @patch("jira_creator.plugins.create_issue_plugin.EnvFetcher")
    def test_execute_successful_with_ai(self, mock_env_fetcher, mock_template_loader):
        """Test successful execution with AI enhancement."""
        # Setup mocks
        mock_env_fetcher.get.return_value = "https://jira.example.com"

        # Mock template loader
        mock_loader = Mock()
        mock_loader.get_fields.return_value = ["field1", "field2"]
        mock_loader.get_template.return_value = "Template content"
        mock_loader.render_description.return_value = "Rendered description"
        mock_template_loader.return_value = mock_loader

        # Mock AI provider
        mock_ai = Mock()
        mock_ai.improve_text.return_value = "AI enhanced description"

        plugin = CreateIssuePlugin(ai_provider=mock_ai)
        mock_client = Mock()
        mock_client.request.return_value = {"key": "TEST-123"}

        args = Namespace(type="story", summary="Test Summary", edit=False, dry_run=False, no_ai=False)

        # Mock interactive input
        with patch("builtins.input", side_effect=["value1", "value2"]):
            with patch("builtins.print") as mock_print:
                result = plugin.execute(mock_client, args)

        assert result is True
        mock_ai.improve_text.assert_called_once()
        mock_client.request.assert_called_once()

        # Check success messages
        print_calls = [call[0][0] for call in mock_print.call_args_list]
        assert any("✅ Issue created: TEST-123" in str(call) for call in print_calls)
        assert any("🔗 https://jira.example.com/browse/TEST-123" in str(call) for call in print_calls)

    @patch("jira_creator.plugins.create_issue_plugin.TemplateLoader")
    @patch("jira_creator.plugins.create_issue_plugin.EnvFetcher")
    def test_execute_with_dry_run(self, mock_env_fetcher, mock_template_loader):
        """Test execution in dry run mode."""
        mock_env_fetcher.get.return_value = "https://jira.example.com"

        # Mock template loader
        mock_loader = Mock()
        mock_loader.get_fields.return_value = ["field1"]
        mock_loader.get_template.return_value = "Template content"
        mock_loader.render_description.return_value = "Rendered description"
        mock_template_loader.return_value = mock_loader

        plugin = CreateIssuePlugin()
        mock_client = Mock()

        args = Namespace(type="bug", summary="Bug Summary", edit=False, dry_run=True, no_ai=True)

        with patch("builtins.input", return_value="value1"):
            with patch("builtins.print") as mock_print:
                result = plugin.execute(mock_client, args)

        assert result is True
        mock_client.request.assert_not_called()  # Should not make API call

        # Check dry run output
        print_calls = [str(call) for call in mock_print.call_args_list]
        assert any("DRY RUN - Issue Preview" in str(call) for call in print_calls)
        assert any("Bug Summary" in str(call) for call in print_calls)

    @patch("jira_creator.plugins.create_issue_plugin.TemplateLoader")
    def test_execute_with_editor(self, mock_template_loader):
        """Test execution with editor mode."""
        # Mock template loader
        mock_loader = Mock()
        mock_loader.get_fields.return_value = ["field1", "field2"]
        mock_loader.get_template.return_value = "Template content"
        mock_loader.render_description.return_value = "Initial description"
        mock_template_loader.return_value = mock_loader

        # Mock editor function
        def mock_editor(cmd_list):
            filename = cmd_list[1]
            with open(filename, "w") as f:
                f.write("Edited description")

        plugin = CreateIssuePlugin(editor_func=mock_editor)
        mock_client = Mock()
        mock_client.request.return_value = {"key": "TEST-456"}

        args = Namespace(type="task", summary="Task Summary", edit=True, dry_run=False, no_ai=True)

        with patch("builtins.print"):
            result = plugin.execute(mock_client, args)

        assert result is True

        # Verify edited description was used
        call_args = mock_client.request.call_args
        payload = call_args[1]["json_data"]
        assert payload["fields"]["description"] == "Edited description"

    @patch("jira_creator.plugins.create_issue_plugin.TemplateLoader")
    def test_execute_with_ai_error(self, mock_template_loader):
        """Test execution when AI enhancement fails."""
        # Mock template loader
        mock_loader = Mock()
        mock_loader.get_fields.return_value = ["field1"]
        mock_loader.get_template.return_value = "Template"
        mock_loader.render_description.return_value = "Original description"
        mock_template_loader.return_value = mock_loader

        # Mock AI provider that fails
        mock_ai = Mock()
        mock_ai.improve_text.side_effect = AiError("AI service unavailable")

        plugin = CreateIssuePlugin(ai_provider=mock_ai)
        mock_client = Mock()
        mock_client.request.return_value = {"key": "TEST-789"}

        args = Namespace(type="task", summary="Task Summary", edit=False, dry_run=False, no_ai=False)

        with patch("builtins.input", return_value="value1"):
            with patch("builtins.print") as mock_print:
                result = plugin.execute(mock_client, args)

        assert result is True

        # Check AI error message
        print_calls = [call[0][0] for call in mock_print.call_args_list]
        assert any("⚠️  AI enhancement failed, using original text" in str(call) for call in print_calls)

        # Verify original description was used
        call_args = mock_client.request.call_args
        assert call_args[1]["json_data"]["fields"]["description"] == "Original description"

    @patch("jira_creator.plugins.create_issue_plugin.TemplateLoader")
    def test_execute_with_create_error(self, mock_template_loader):
        """Test execution when issue creation fails."""
        # Mock template loader
        mock_loader = Mock()
        mock_loader.get_fields.return_value = []
        mock_loader.get_template.return_value = "Template"
        mock_loader.render_description.return_value = "Description"
        mock_template_loader.return_value = mock_loader

        plugin = CreateIssuePlugin()
        mock_client = Mock()
        mock_client.request.side_effect = CreateIssueError("API error")

        args = Namespace(type="story", summary="Story Summary", edit=False, dry_run=False, no_ai=True)

        with patch("builtins.print") as mock_print:
            with pytest.raises(CreateIssueError):
                plugin.execute(mock_client, args)

        # Check error message
        print_calls = [call[0][0] for call in mock_print.call_args_list]
        assert any("❌ Failed to create issue" in str(call) for call in print_calls)

    @patch("jira_creator.plugins.create_issue_plugin.TemplateLoader")
    def test_gather_field_values_interactive(self, mock_template_loader):
        """Test gathering field values in interactive mode."""
        plugin = CreateIssuePlugin()
        fields = ["field1", "field2", "field3"]

        with patch("builtins.input", side_effect=["value1", "value2", "value3"]):
            with patch("builtins.print"):
                values = plugin._gather_field_values(fields, edit_mode=False)

        assert values == {"field1": "value1", "field2": "value2", "field3": "value3"}

    def test_gather_field_values_edit_mode(self):
        """Test gathering field values in edit mode."""
        plugin = CreateIssuePlugin()
        fields = ["field1", "field2"]

        values = plugin._gather_field_values(fields, edit_mode=True)

        assert values == {"field1": "{{field1}}", "field2": "{{field2}}"}

    @patch("jira_creator.plugins.create_issue_plugin.get_ai_provider")
    @patch("jira_creator.plugins.create_issue_plugin.EnvFetcher")
    def test_enhance_with_ai(self, mock_env_fetcher, mock_get_ai_provider):
        """Test AI enhancement method."""
        mock_env_fetcher.get.return_value = "openai"

        mock_ai = Mock()
        mock_ai.improve_text.return_value = "Enhanced text"
        mock_get_ai_provider.return_value = mock_ai

        plugin = CreateIssuePlugin()
        result = plugin._enhance_with_ai("Original text", "story")

        assert result == "Enhanced text"
        mock_get_ai_provider.assert_called_once_with("openai")

    @patch("jira_creator.plugins.create_issue_plugin.EnvFetcher")
    def test_build_payload_basic(self, mock_env_fetcher):
        """Test building basic payload."""
        mock_env_fetcher.get.side_effect = lambda key: {
            "JIRA_PROJECT_KEY": "TEST",
            "JIRA_AFFECTS_VERSION": "",
            "JIRA_COMPONENT_NAME": "",
            "JIRA_PRIORITY": "Normal",
            "JIRA_EPIC_FIELD": "",
        }.get(key, "")

        plugin = CreateIssuePlugin()
        payload = plugin._build_payload("Test Summary", "Test Description", "bug")

        assert payload == {
            "fields": {
                "project": {"key": "TEST"},
                "summary": "Test Summary",
                "description": "Test Description",
                "issuetype": {"name": "Bug"},
                "priority": {"name": "Normal"},
            }
        }

    @patch("jira_creator.plugins.create_issue_plugin.EnvFetcher")
    def test_build_payload_with_optional_fields(self, mock_env_fetcher):
        """Test building payload with all optional fields."""
        mock_env_fetcher.get.side_effect = lambda key, default=None: {
            "JIRA_PROJECT_KEY": "TEST",
            "JIRA_AFFECTS_VERSION": "1.0",
            "JIRA_COMPONENT_NAME": "Backend",
            "JIRA_PRIORITY": "High",
            "JIRA_EPIC_FIELD": "customfield_10001",
            "JIRA_EPIC_KEY": "TEST-100",
        }.get(key, default if default is not None else "")

        plugin = CreateIssuePlugin()
        payload = plugin._build_payload("Story Summary", "Story Description", "story")

        assert payload == {
            "fields": {
                "project": {"key": "TEST"},
                "summary": "Story Summary",
                "description": "Story Description",
                "issuetype": {"name": "Story"},
                "priority": {"name": "High"},
                "versions": [{"name": "1.0"}],
                "components": [{"name": "Backend"}],
                "customfield_10001": "TEST-100",
            }
        }

    def test_show_dry_run(self):
        """Test dry run output display."""
        plugin = CreateIssuePlugin()

        payload = {
            "fields": {
                "project": {"key": "TEST"},
                "summary": "Test Summary",
                "description": "Test Description",
            }
        }

        with patch("builtins.print") as mock_print:
            plugin._show_dry_run("Test Summary", "Test Description", payload)

        # Check all expected output elements
        print_calls = [call[0][0] for call in mock_print.call_args_list]
        assert any("DRY RUN - Issue Preview" in str(call) for call in print_calls)
        assert any("📋 Summary: Test Summary" in str(call) for call in print_calls)
        assert any("📄 Description:" in str(call) for call in print_calls)
        assert any("Test Description" in str(call) for call in print_calls)
        assert any("🔧 JSON Payload:" in str(call) for call in print_calls)

    @patch("jira_creator.plugins.create_issue_plugin.TemplateLoader")
    def test_execute_with_empty_template(self, mock_template_loader):
        """Test execution with empty template."""
        # Mock template loader that returns empty fields
        mock_loader = Mock()
        mock_loader.get_fields.return_value = []
        mock_loader.get_template.return_value = ""
        mock_loader.render_description.return_value = ""
        mock_template_loader.return_value = mock_loader

        plugin = CreateIssuePlugin()
        mock_client = Mock()
        mock_client.request.return_value = {"key": "TEST-999"}

        args = Namespace(type="epic", summary="Epic Summary", edit=False, dry_run=False, no_ai=True)

        result = plugin.execute(mock_client, args)

        assert result is True
        # Verify empty description was used
        call_args = mock_client.request.call_args
        assert call_args[1]["json_data"]["fields"]["description"] == ""

    @patch("jira_creator.plugins.create_issue_plugin.TemplateLoader")
    @patch("os.environ.get")
    def test_edit_description_with_custom_editor(self, mock_env_get, mock_template_loader):
        """Test editing description with custom editor from environment."""
        mock_env_get.return_value = "nano"

        # Mock editor function
        mock_editor = Mock()

        plugin = CreateIssuePlugin(editor_func=mock_editor)
        plugin._edit_description("Test description")

        # Verify custom editor was used
        mock_editor.assert_called_once()
        call_args = mock_editor.call_args[0][0]
        assert call_args[0] == "nano"
        assert call_args[1].endswith(".md")

    @patch("jira_creator.plugins.create_issue_plugin.TemplateLoader")
    def test_execute_all_issue_types(self, mock_template_loader):
        """Test execution with all supported issue types."""
        issue_types = ["bug", "story", "epic", "task"]

        for issue_type in issue_types:
            # Reset mocks for each iteration
            mock_loader = Mock()
            mock_loader.get_fields.return_value = []
            mock_loader.get_template.return_value = "Template"
            mock_loader.render_description.return_value = "Description"
            mock_template_loader.return_value = mock_loader

            plugin = CreateIssuePlugin()
            mock_client = Mock()
            mock_client.request.return_value = {"key": f"TEST-{issue_type.upper()}"}

            args = Namespace(
                type=issue_type,
                summary=f"{issue_type} Summary",
                edit=False,
                dry_run=False,
                no_ai=True,
            )

            result = plugin.execute(mock_client, args)
            assert result is True

            # Verify correct issue type was used
            call_args = mock_client.request.call_args
            payload = call_args[1]["json_data"]
            assert payload["fields"]["issuetype"]["name"] == issue_type.capitalize()

    @patch("jira_creator.plugins.create_issue_plugin.TemplateLoader")
    def test_execute_with_file_not_found(self, mock_template_loader):
        """Test execution when template file is not found."""
        mock_template_loader.side_effect = FileNotFoundError("Template not found")

        plugin = CreateIssuePlugin()
        mock_client = Mock()

        args = Namespace(type="story", summary="Test Summary", edit=False, dry_run=False, no_ai=True)

        with pytest.raises(FileNotFoundError):
            plugin.execute(mock_client, args)

    def test_dependency_injection(self):
        """Test dependency injection mechanism."""
        # Test with injected dependencies
        mock_ai = Mock()
        mock_editor = Mock()

        plugin = CreateIssuePlugin(ai_provider=mock_ai, editor_func=mock_editor)

        assert plugin.get_dependency("ai_provider") == mock_ai
        assert plugin.get_dependency("editor_func") == mock_editor
        assert plugin.get_dependency("nonexistent", "default") == "default"

    @patch("jira_creator.plugins.create_issue_plugin.subprocess.call")
    def test_edit_description_default_behavior(self, mock_subprocess):
        """Test edit description with default subprocess behavior."""
        plugin = CreateIssuePlugin()

        with patch("tempfile.NamedTemporaryFile") as mock_temp:
            mock_file = Mock()
            mock_file.name = "/tmp/test.md"
            mock_file.read.return_value = "Edited content"
            mock_temp.return_value.__enter__.return_value = mock_file

            result = plugin._edit_description("Original content")

        assert result == "Edited content"
        mock_subprocess.assert_called_once()
