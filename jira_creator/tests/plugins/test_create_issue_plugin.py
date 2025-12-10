#!/usr/bin/env python
"""Tests for the create issue plugin."""

from argparse import ArgumentParser, Namespace
from unittest.mock import Mock, mock_open, patch

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

        # Check that arguments are registered (now includes additional ones)
        # We have: type, summary, -e/--edit, --dry-run, --no-ai, --input-file, --story-points, --output, --quiet
        assert mock_parser.add_argument.call_count == 9

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

        args = Namespace(
            type="story",
            summary="Test Summary",
            edit=False,
            dry_run=False,
            no_ai=False,
            input_file=None,
            story_points=None,
            output="text",
            quiet=False,
        )

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

        args = Namespace(
            type="bug",
            summary="Bug Summary",
            edit=False,
            dry_run=True,
            no_ai=True,
            input_file=None,
            story_points=None,
            output="text",
            quiet=False,
        )

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

        args = Namespace(
            type="task",
            summary="Task Summary",
            edit=True,
            dry_run=False,
            no_ai=True,
            input_file=None,
            story_points=None,
            output="text",
            quiet=False,
        )

        with patch("builtins.print"):
            result = plugin.execute(mock_client, args)

        assert result is True

        # Verify edited description was used
        call_args = mock_client.request.call_args
        payload = call_args[1]["json_data"]
        assert payload["fields"]["description"] == "Edited description"

    @patch("jira_creator.plugins.create_issue_plugin.TemplateLoader")
    def test_execute_with_ai_error(self, mock_template_loader):
        """Test execution when AI enhancement fails - should abort issue creation."""
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

        args = Namespace(
            type="task",
            summary="Task Summary",
            edit=False,
            dry_run=False,
            no_ai=False,
            input_file=None,
            story_points=None,
            output="text",
            quiet=False,
        )

        with patch("builtins.input", return_value="value1"):
            with patch("builtins.print") as mock_print:
                result = plugin.execute(mock_client, args)

        # Should return False to indicate failure
        assert result is False

        # Check AI error message
        print_calls = [call[0][0] for call in mock_print.call_args_list]
        assert any("❌ AI enhancement failed" in str(call) for call in print_calls)
        assert any("⚠️  Issue creation aborted" in str(call) for call in print_calls)

        # Verify issue was NOT created
        mock_client.request.assert_not_called()

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

        args = Namespace(
            type="story",
            summary="Story Summary",
            edit=False,
            dry_run=False,
            no_ai=True,
            input_file=None,
            story_points=None,
            output="text",
            quiet=False,
        )

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
                "versions": [{"name": "2.5"}],
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

    @patch("jira_creator.plugins.create_issue_plugin.EnvFetcher")
    def test_build_payload_bug_with_template_version(self, mock_env_fetcher):
        """Test building payload for bug with affected version from template field."""
        mock_env_fetcher.get.side_effect = lambda key: {
            "JIRA_PROJECT_KEY": "TEST",
            "JIRA_AFFECTS_VERSION": "",
            "JIRA_COMPONENT_NAME": "",
            "JIRA_PRIORITY": "Normal",
            "JIRA_EPIC_FIELD": "",
        }.get(key, "")

        plugin = CreateIssuePlugin()
        field_values = {"Affected Version": "2.1.3"}
        payload = plugin._build_payload("Bug Summary", "Bug Description", "bug", field_values)

        assert payload == {
            "fields": {
                "project": {"key": "TEST"},
                "summary": "Bug Summary",
                "description": "Bug Description",
                "issuetype": {"name": "Bug"},
                "priority": {"name": "Normal"},
                "versions": [{"name": "2.1.3"}],
            }
        }

    @patch("jira_creator.plugins.create_issue_plugin.EnvFetcher")
    def test_build_payload_bug_env_version_fallback(self, mock_env_fetcher):
        """Test building payload for bug with affected version from environment."""
        mock_env_fetcher.get.side_effect = lambda key: {
            "JIRA_PROJECT_KEY": "TEST",
            "JIRA_AFFECTS_VERSION": "1.0.0",
            "JIRA_COMPONENT_NAME": "",
            "JIRA_PRIORITY": "Normal",
            "JIRA_EPIC_FIELD": "",
        }.get(key, "")

        plugin = CreateIssuePlugin()
        field_values = {"Affected Version": ""}  # Empty template field
        payload = plugin._build_payload("Bug Summary", "Bug Description", "bug", field_values)

        assert payload == {
            "fields": {
                "project": {"key": "TEST"},
                "summary": "Bug Summary",
                "description": "Bug Description",
                "issuetype": {"name": "Bug"},
                "priority": {"name": "Normal"},
                "versions": [{"name": "1.0.0"}],
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

        args = Namespace(
            type="epic",
            summary="Epic Summary",
            edit=False,
            dry_run=False,
            no_ai=True,
            input_file=None,
            story_points=None,
            output="text",
            quiet=False,
        )

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
                input_file=None,
                story_points=None,
                output="text",
                quiet=False,
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

        args = Namespace(
            type="story",
            summary="Test Summary",
            edit=False,
            dry_run=False,
            no_ai=True,
            input_file=None,
            story_points=None,
            output="text",
            quiet=False,
        )

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
    @patch("builtins.open", new_callable=mock_open, read_data="Edited content")
    def test_edit_description_default_behavior(self, mock_file_open, mock_subprocess):
        """Test edit description with default subprocess behavior."""
        plugin = CreateIssuePlugin()

        with patch("tempfile.NamedTemporaryFile") as mock_temp:
            mock_file = Mock()
            mock_file.name = "/tmp/test.md"
            mock_file.write.return_value = None
            mock_file.flush.return_value = None
            mock_temp.return_value.__enter__.return_value = mock_file

            with patch("os.unlink") as mock_unlink:
                result = plugin._edit_description("Original content")

        assert result == "Edited content"
        mock_subprocess.assert_called_once()
        mock_unlink.assert_called_once_with("/tmp/test.md")

    def test_load_field_values_from_yaml(self):
        """Test loading field values from YAML file."""
        plugin = CreateIssuePlugin()
        yaml_content = """
User Story: "As a user, I want feature X"
Acceptance Criteria: "* [ ] Item 1"
Supporting Documentation: "See docs"
Definition of Done: "Tests pass"
"""
        expected_fields = ["User Story", "Acceptance Criteria", "Supporting Documentation", "Definition of Done"]

        with patch("builtins.open", mock_open(read_data=yaml_content)):
            with patch("pathlib.Path.exists", return_value=True):
                result = plugin._load_field_values_from_file("test.yaml", expected_fields)

        assert result["User Story"] == "As a user, I want feature X"
        assert result["Acceptance Criteria"] == "* [ ] Item 1"

    def test_load_field_values_yaml_parse_error(self):
        """Test YAML parsing error handling."""
        plugin = CreateIssuePlugin()
        invalid_yaml = "invalid: yaml: content: [unclosed"
        expected_fields = ["field1"]

        with patch("builtins.open", mock_open(read_data=invalid_yaml)):
            with patch("pathlib.Path.exists", return_value=True):
                with pytest.raises(CreateIssueError, match="Failed to parse input file"):
                    plugin._load_field_values_from_file("test.yaml", expected_fields)

    def test_load_field_values_missing_fields(self):
        """Test missing required fields error."""
        plugin = CreateIssuePlugin()
        json_content = '{"field1": "value1"}'
        expected_fields = ["field1", "field2", "field3"]

        with patch("builtins.open", mock_open(read_data=json_content)):
            with patch("pathlib.Path.exists", return_value=True):
                with pytest.raises(CreateIssueError, match="Missing required fields"):
                    plugin._load_field_values_from_file("test.json", expected_fields)

    def test_load_field_values_file_read_error(self):
        """Test file I/O error handling."""
        plugin = CreateIssuePlugin()
        expected_fields = ["field1"]

        with patch("builtins.open", side_effect=OSError("Permission denied")):
            with patch("pathlib.Path.exists", return_value=True):
                with pytest.raises(CreateIssueError, match="Failed to read input file"):
                    plugin._load_field_values_from_file("test.json", expected_fields)

    @patch("builtins.print")
    def test_validate_length_failure(self, mock_print):
        """Test validation length failure."""
        plugin = CreateIssuePlugin()

        result = plugin._validate_length("Summary", 300, 255, "✓ Summary length: 300/255 characters")

        assert result is False
        assert any("❌ Summary exceeds 255 character limit" in str(call) for call in mock_print.call_args_list)

    @patch("builtins.print")
    @patch("jira_creator.plugins.create_issue_plugin.EnvFetcher")
    def test_check_epic_link_with_epic(self, mock_env_fetcher, mock_print):
        """Test epic link check when epic is present."""
        plugin = CreateIssuePlugin()
        mock_env_fetcher.get.return_value = "customfield_12311140"

        fields = {"issuetype": {"name": "Story"}, "customfield_12311140": "AAP-123"}

        plugin._check_epic_link(fields)

        assert any("✓ Epic link: AAP-123" in str(call) for call in mock_print.call_args_list)

    @patch("builtins.print")
    @patch("jira_creator.plugins.create_issue_plugin.EnvFetcher")
    def test_check_epic_link_without_epic(self, mock_env_fetcher, mock_print):
        """Test epic link check when epic is missing."""
        plugin = CreateIssuePlugin()
        mock_env_fetcher.get.return_value = "customfield_12311140"

        fields = {"issuetype": {"name": "Story"}}

        plugin._check_epic_link(fields)

        assert any("⚠️  No epic link specified for story" in str(call) for call in mock_print.call_args_list)

    @patch("builtins.print")
    def test_output_result_quiet_mode(self, mock_print):
        """Test output in quiet mode."""
        plugin = CreateIssuePlugin()
        args = Mock(quiet=True, output=None)

        plugin._output_result(args, "TEST-123", "10001", "https://jira.example.com", None)

        # Should only print the issue key
        mock_print.assert_called_once_with("TEST-123")

    @patch("builtins.print")
    def test_output_result_json_mode(self, mock_print):
        """Test output in JSON mode."""
        plugin = CreateIssuePlugin()
        args = Mock(quiet=False, output="json")

        plugin._output_result(args, "TEST-123", "10001", "https://jira.example.com", None)

        # Should print JSON
        call_args = str(mock_print.call_args_list[0])
        assert "TEST-123" in call_args
        assert "10001" in call_args

    @patch("builtins.print")
    def test_output_result_json_mode_with_story_points(self, mock_print):
        """Test output in JSON mode with story points."""
        plugin = CreateIssuePlugin()
        args = Mock(quiet=False, output="json")

        plugin._output_result(args, "TEST-123", "10001", "https://jira.example.com", 5)

        # Should print JSON with story points
        call_args = str(mock_print.call_args_list[0])
        assert "story_points" in call_args
        assert "5" in call_args

    @patch("builtins.print")
    def test_output_result_default_with_story_points(self, mock_print):
        """Test default output with story points."""
        plugin = CreateIssuePlugin()
        args = Mock(quiet=False, output=None)

        plugin._output_result(args, "TEST-123", "10001", "https://jira.example.com", 3)

        # Should print story points
        assert any("📊 Story points: 3" in str(call) for call in mock_print.call_args_list)

    def test_load_field_values_file_not_found(self):
        """Test _load_field_values_from_file when file doesn't exist - covers line 187."""
        plugin = CreateIssuePlugin()
        expected_fields = ["field1"]

        with patch("pathlib.Path.exists", return_value=False):
            with pytest.raises(CreateIssueError, match="Input file not found"):
                plugin._load_field_values_from_file("nonexistent.json", expected_fields)

    @patch("jira_creator.plugins.create_issue_plugin.TemplateLoader")
    @patch("jira_creator.plugins.create_issue_plugin.EnvFetcher")
    def test_execute_with_input_file(self, mock_env_fetcher, mock_template_loader):
        """Test execute with input file - covers line 107."""
        mock_env_fetcher.get.return_value = "https://jira.example.com"

        # Mock template loader
        mock_loader = Mock()
        mock_loader.get_fields.return_value = ["field1", "field2"]
        mock_loader.render_description.return_value = "Rendered description"
        mock_template_loader.return_value = mock_loader

        plugin = CreateIssuePlugin()
        mock_client = Mock()
        mock_client.request.return_value = {"key": "TEST-123", "id": "10001"}

        args = Namespace(
            type="story",
            summary="Test Summary",
            edit=False,
            dry_run=False,
            no_ai=True,
            input_file="test.json",
            story_points=None,
            output="text",
            quiet=False,
        )

        # Mock file loading
        json_content = '{"field1": "value1", "field2": "value2"}'
        with patch("builtins.open", mock_open(read_data=json_content)):
            with patch("pathlib.Path.exists", return_value=True):
                with patch("builtins.print"):
                    result = plugin.execute(mock_client, args)

        assert result is True
        mock_client.request.assert_called_once()

    @patch("jira_creator.plugins.create_issue_plugin.TemplateLoader")
    @patch("jira_creator.plugins.create_issue_plugin.EnvFetcher")
    def test_execute_with_story_points(self, mock_env_fetcher, mock_template_loader):
        """Test execute with story points - covers lines 132-133."""
        mock_env_fetcher.get.side_effect = lambda key, default=None: {
            "JIRA_URL": "https://jira.example.com",
            "JIRA_STORY_POINTS_FIELD": "customfield_12310243",
        }.get(key, default)

        # Mock template loader
        mock_loader = Mock()
        mock_loader.get_fields.return_value = []
        mock_loader.render_description.return_value = "Description"
        mock_template_loader.return_value = mock_loader

        plugin = CreateIssuePlugin()
        mock_client = Mock()
        mock_client.request.return_value = {"key": "TEST-123", "id": "10001"}

        args = Namespace(
            type="story",
            summary="Story with points",
            edit=False,
            dry_run=False,
            no_ai=True,
            input_file=None,
            story_points=5,
            output="text",
            quiet=False,
        )

        with patch("builtins.print"):
            result = plugin.execute(mock_client, args)

        assert result is True

        # Verify story points field was added to payload
        call_args = mock_client.request.call_args
        payload = call_args[1]["json_data"]
        assert payload["fields"]["customfield_12310243"] == 5
