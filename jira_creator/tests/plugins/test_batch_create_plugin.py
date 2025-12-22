#!/usr/bin/env python
"""Tests for the batch create plugin."""

from argparse import ArgumentParser, Namespace
from pathlib import Path
from unittest.mock import Mock, mock_open, patch

import pytest

from jira_creator.core.env_fetcher import EnvFetcher
from jira_creator.plugins.batch_create_plugin import BatchCreateError, BatchCreatePlugin

# Add logging environment variables to EnvFetcher vars for testing
if not hasattr(EnvFetcher, "vars"):
    EnvFetcher.vars = {}

for var in ["JIRA_LOG_LEVEL", "JIRA_LOG_FILE", "JIRA_LOG_FORMAT"]:
    if var not in EnvFetcher.vars:
        EnvFetcher.vars[var] = ""


class TestBatchCreatePlugin:
    """Test cases for BatchCreatePlugin."""

    def test_plugin_properties(self):
        """Test plugin properties are set correctly."""
        plugin = BatchCreatePlugin()
        assert plugin.command_name == "batch-create"
        assert "multiple" in plugin.help_text.lower()

    def test_register_arguments(self):
        """Test argument registration."""
        plugin = BatchCreatePlugin()
        mock_parser = Mock(spec=ArgumentParser)

        plugin.register_arguments(mock_parser)

        # Verify expected arguments are registered
        assert mock_parser.add_argument.call_count == 8

    def test_rest_operation(self):
        """Test the REST operation directly."""
        plugin = BatchCreatePlugin()
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

        assert result == mock_response
        mock_client.request.assert_called_once_with("POST", "/rest/api/2/issue/", json_data=payload)

    @patch("jira_creator.plugins.batch_create_plugin.Path")
    def test_execute_directory_not_found(self, mock_path):
        """Test execution when input directory doesn't exist."""
        plugin = BatchCreatePlugin()
        mock_client = Mock()

        mock_path_instance = Mock()
        mock_path_instance.exists.return_value = False
        mock_path.return_value = mock_path_instance

        args = Namespace(
            issue_type="story",
            input_dir="/nonexistent",
            pattern="*.json",
            epic=None,
            no_ai=True,
            dry_run=False,
            output="text",
            continue_on_error=False,
        )

        with pytest.raises(BatchCreateError, match="Input directory not found"):
            plugin.execute(mock_client, args)

    @patch("jira_creator.plugins.batch_create_plugin.Path")
    def test_execute_no_files_found(self, mock_path):
        """Test execution when no files match pattern."""
        plugin = BatchCreatePlugin()
        mock_client = Mock()

        mock_path_instance = Mock()
        mock_path_instance.exists.return_value = True
        mock_path_instance.is_dir.return_value = True
        mock_path_instance.glob.return_value = []
        mock_path.return_value = mock_path_instance

        args = Namespace(
            issue_type="story",
            input_dir="/some/dir",
            pattern="*.json",
            epic=None,
            no_ai=True,
            dry_run=False,
            output="text",
            continue_on_error=False,
        )

        with pytest.raises(BatchCreateError, match="No files matching pattern"):
            plugin.execute(mock_client, args)

    def test_load_file_json(self):
        """Test loading JSON file."""
        plugin = BatchCreatePlugin()

        json_content = '{"field1": "value1", "field2": "value2"}'
        mock_file = mock_open(read_data=json_content)

        with patch("builtins.open", mock_file):
            result = plugin._load_file(Path("test.json"))  # pylint: disable=protected-access

        assert result == {"field1": "value1", "field2": "value2"}

    def test_load_file_yaml(self):
        """Test loading YAML file."""
        plugin = BatchCreatePlugin()

        yaml_content = "field1: value1\nfield2: value2\n"
        mock_file = mock_open(read_data=yaml_content)

        with patch("builtins.open", mock_file):
            result = plugin._load_file(Path("test.yaml"))  # pylint: disable=protected-access

        assert result == {"field1": "value1", "field2": "value2"}

    def test_load_file_parse_error(self):
        """Test loading file with parse errors."""
        plugin = BatchCreatePlugin()

        invalid_content = "invalid: yaml: content: [unclosed"
        mock_file = mock_open(read_data=invalid_content)

        with patch("builtins.open", mock_file):
            with pytest.raises(BatchCreateError, match="Failed to parse"):
                plugin._load_file(Path("test.yaml"))  # pylint: disable=protected-access

    def test_load_file_io_error(self):
        """Test loading file with IO error."""
        plugin = BatchCreatePlugin()

        with patch("builtins.open", side_effect=OSError("Permission denied")):
            with pytest.raises(BatchCreateError, match="Failed to read"):
                plugin._load_file(Path("test.json"))  # pylint: disable=protected-access

    @patch("jira_creator.plugins.batch_create_plugin.EnvFetcher")
    def test_build_payload_basic(self, mock_env_fetcher):
        """Test building basic payload."""
        plugin = BatchCreatePlugin()
        mock_env_fetcher.get.side_effect = lambda key, default=None: {
            "JIRA_PROJECT_KEY": "TEST",
            "JIRA_PRIORITY": "Normal",
        }.get(key, default)

        payload = plugin._build_payload(  # pylint: disable=protected-access
            "Test Summary", "Test Description", "story", {}
        )

        assert payload["fields"]["summary"] == "Test Summary"
        assert payload["fields"]["description"] == "Test Description"
        assert payload["fields"]["project"]["key"] == "TEST"
        assert payload["fields"]["issuetype"]["name"] == "Story"
        assert payload["fields"]["priority"]["name"] == "Normal"

    @patch("jira_creator.plugins.batch_create_plugin.EnvFetcher")
    def test_build_payload_bug_with_version(self, mock_env_fetcher):
        """Test building payload for bug with affects version."""
        plugin = BatchCreatePlugin()
        mock_env_fetcher.get.side_effect = lambda key, default=None: {
            "JIRA_PROJECT_KEY": "TEST",
            "JIRA_PRIORITY": "Normal",
        }.get(key, default)

        field_values = {"Affects Version": "1.0.0"}
        payload = plugin._build_payload(  # pylint: disable=protected-access
            "Bug Summary", "Bug Description", "bug", field_values
        )

        assert payload["fields"]["issuetype"]["name"] == "Bug"
        assert payload["fields"]["versions"] == [{"name": "1.0.0"}]

    @patch("builtins.print")
    @patch("jira_creator.plugins.batch_create_plugin.EnvFetcher")
    @patch("jira_creator.plugins.batch_create_plugin.TemplateLoader")
    @patch("jira_creator.plugins.batch_create_plugin.Path")
    def test_execute_dry_run(
        self, mock_path_cls, mock_template_loader, mock_env_fetcher, mock_print
    ):  # pylint: disable=unused-argument
        """Test execution in dry-run mode."""
        plugin = BatchCreatePlugin()
        mock_client = Mock()

        # Setup mock file paths
        mock_file1 = Mock(spec=Path)
        mock_file1.name = "story1.json"
        mock_file1.stem = "story1"

        mock_dir = Mock()
        mock_dir.exists.return_value = True
        mock_dir.is_dir.return_value = True
        mock_dir.glob.return_value = [mock_file1]
        mock_path_cls.return_value = mock_dir

        # Setup template loader
        mock_loader_instance = Mock()
        mock_loader_instance.get_fields.return_value = ["User Story", "Acceptance Criteria"]
        mock_loader_instance.render_description.return_value = "Description"
        mock_template_loader.return_value = mock_loader_instance

        # Setup env fetcher
        mock_env_fetcher.get.side_effect = lambda key, default=None: {
            "JIRA_PROJECT_KEY": "TEST",
            "JIRA_PRIORITY": "Normal",
        }.get(key, default)

        # Mock file loading
        file_content = {"User Story": "As a user", "Acceptance Criteria": "Tests pass"}
        with patch.object(plugin, "_load_file", return_value=file_content):
            args = Namespace(
                issue_type="story",
                input_dir="/test/dir",
                pattern="*.json",
                epic=None,
                no_ai=True,
                dry_run=True,
                output="text",
                continue_on_error=False,
            )

            result = plugin.execute(mock_client, args)

        assert result is True
        # Verify client was not called (dry run)
        mock_client.request.assert_not_called()

    @patch("builtins.print")
    @patch("jira_creator.plugins.batch_create_plugin.EnvFetcher")
    @patch("jira_creator.plugins.batch_create_plugin.TemplateLoader")
    @patch("jira_creator.plugins.batch_create_plugin.Path")
    def test_execute_success(
        self, mock_path_cls, mock_template_loader, mock_env_fetcher, mock_print
    ):  # pylint: disable=unused-argument
        """Test successful batch creation."""
        plugin = BatchCreatePlugin()
        mock_client = Mock()
        mock_client.request.return_value = {"key": "TEST-123", "id": "10001"}

        # Setup mock file paths
        mock_file1 = Mock(spec=Path)
        mock_file1.name = "story1.json"
        mock_file1.stem = "story1"

        mock_dir = Mock()
        mock_dir.exists.return_value = True
        mock_dir.is_dir.return_value = True
        mock_dir.glob.return_value = [mock_file1]
        mock_path_cls.return_value = mock_dir

        # Setup template loader
        mock_loader_instance = Mock()
        mock_loader_instance.get_fields.return_value = ["User Story", "Acceptance Criteria"]
        mock_loader_instance.render_description.return_value = "Description"
        mock_template_loader.return_value = mock_loader_instance

        # Setup env fetcher
        mock_env_fetcher.get.side_effect = lambda key, default=None: {
            "JIRA_PROJECT_KEY": "TEST",
            "JIRA_PRIORITY": "Normal",
            "JIRA_URL": "https://jira.example.com",
        }.get(key, default)

        # Mock file loading
        file_content = {"User Story": "As a user", "Acceptance Criteria": "Tests pass"}
        with patch.object(plugin, "_load_file", return_value=file_content):
            args = Namespace(
                issue_type="story",
                input_dir="/test/dir",
                pattern="*.json",
                epic=None,
                no_ai=True,
                dry_run=False,
                output="text",
                continue_on_error=False,
            )

            result = plugin.execute(mock_client, args)

        assert result is True
        mock_client.request.assert_called_once()

    @patch("builtins.print")
    @patch("jira_creator.plugins.batch_create_plugin.EnvFetcher")
    def test_output_results_json(self, mock_env_fetcher, mock_print):
        """Test JSON output format."""
        plugin = BatchCreatePlugin()
        mock_env_fetcher.get.return_value = "https://jira.example.com"

        args = Namespace(output="json")
        results = [{"key": "TEST-123", "id": "10001", "title": "Test Issue", "file": "test.json"}]
        errors = []

        plugin._output_results(args, results, errors)  # pylint: disable=protected-access

        # Verify JSON was printed
        assert mock_print.called
        output_str = str(mock_print.call_args[0][0])
        assert "TEST-123" in output_str

    @patch("builtins.print")
    @patch("jira_creator.plugins.batch_create_plugin.EnvFetcher")
    def test_output_results_text_with_errors(self, mock_env_fetcher, mock_print):
        """Test text output format with errors."""
        plugin = BatchCreatePlugin()
        mock_env_fetcher.get.return_value = "https://jira.example.com"

        args = Namespace(output="text")
        results = [{"key": "TEST-123", "id": "10001", "title": "Test Issue", "file": "test.json"}]
        errors = [{"file": "error.json", "error": "Missing fields"}]

        plugin._output_results(args, results, errors)  # pylint: disable=protected-access

        # Verify text output was printed
        assert mock_print.called
        print_calls = [str(call) for call in mock_print.call_args_list]
        assert any("Successfully created: 1" in call for call in print_calls)
        assert any("Failed: 1" in call for call in print_calls)

    @patch("jira_creator.plugins.batch_create_plugin.EnvFetcher")
    @patch("jira_creator.plugins.batch_create_plugin.TemplateLoader")
    def test_process_file_with_epic(self, mock_template_loader, mock_env_fetcher):
        """Test processing file with epic link."""
        plugin = BatchCreatePlugin()
        mock_client = Mock()
        mock_client.request.return_value = {"key": "TEST-123", "id": "10001"}

        # Setup template loader
        mock_loader_instance = Mock()
        mock_loader_instance.get_fields.return_value = ["User Story"]
        mock_loader_instance.render_description.return_value = "Description"
        mock_template_loader.return_value = mock_loader_instance

        # Setup env fetcher
        mock_env_fetcher.get.side_effect = lambda key, default=None: {
            "JIRA_PROJECT_KEY": "TEST",
            "JIRA_PRIORITY": "Normal",
            "JIRA_EPIC_FIELD": "customfield_12311140",
        }.get(key, default)

        file_content = {"title": "Test Story", "User Story": "As a user"}
        with patch.object(plugin, "_load_file", return_value=file_content):
            with patch("builtins.print"):
                args = Namespace(
                    issue_type="story", epic="EPIC-123", no_ai=True, dry_run=False, continue_on_error=False
                )

                result = plugin._process_file(mock_client, Path("test.json"), args)  # pylint: disable=protected-access

        assert result["key"] == "TEST-123"
        # Verify epic was added to payload
        call_args = mock_client.request.call_args
        payload = call_args[1]["json_data"]
        assert payload["fields"]["customfield_12311140"] == "EPIC-123"

    def test_execute_with_continue_on_error(self, tmp_path):
        """Test batch create with continue-on-error flag."""
        plugin = BatchCreatePlugin()
        mock_client = Mock()

        # Create test files - one good, one bad
        good_file = tmp_path / "good.json"
        good_file.write_text('{"summary": "Good", "description": "Test"}')

        bad_file = tmp_path / "bad.json"
        bad_file.write_text('{"summary": "Bad"}')  # Missing description

        # Mock API responses - first succeeds, second fails
        mock_client.request.side_effect = [
            {"key": "TEST-1"},  # Good file succeeds
        ]

        args = Namespace(
            issue_type="story",
            input_dir=str(tmp_path),
            pattern="*.json",
            epic=None,
            no_ai=True,
            dry_run=False,
            output="text",
            continue_on_error=True,
        )

        with patch("builtins.print") as mock_print:
            result = plugin.execute(mock_client, args)

        # Should return False because there was an error
        assert result is False

        # Check error messages
        print_calls = [str(call) for call in mock_print.call_args_list]
        assert any("Failed to process" in call for call in print_calls)

    def test_execute_dry_run_with_errors(self, tmp_path):
        """Test dry run mode with validation errors."""
        plugin = BatchCreatePlugin()
        mock_client = Mock()

        # Create test files with validation errors
        bad_file1 = tmp_path / "bad1.json"
        bad_file1.write_text('{"summary": "Bad"}')  # Missing description

        bad_file2 = tmp_path / "bad2.json"
        bad_file2.write_text('{"description": "Bad"}')  # Missing summary

        args = Namespace(
            issue_type="story",
            input_dir=str(tmp_path),
            pattern="*.json",
            epic=None,
            no_ai=True,
            dry_run=True,
            output="text",
            continue_on_error=True,
        )

        with patch("builtins.print") as mock_print:
            result = plugin.execute(mock_client, args)

        # Should return False because there were errors
        assert result is False

        # Check error messages
        print_calls = [str(call) for call in mock_print.call_args_list]
        assert any("Validation errors" in call for call in print_calls)
        assert any("bad1.json" in call for call in print_calls)
        assert any("bad2.json" in call for call in print_calls)

    @patch("jira_creator.plugins.batch_create_plugin.EnvFetcher")
    def test_build_payload_with_component(self, mock_env, tmp_path):
        """Test payload building with component from environment."""
        mock_env.get.side_effect = lambda key, default="": {
            "JIRA_PROJECT_KEY": "TEST",
            "JIRA_COMPONENT": "my-component",
            "JIRA_PRIORITY": "High",
            "JIRA_EPIC_FIELD": "customfield_10001",
        }.get(key, default)

        plugin = BatchCreatePlugin()
        mock_client = Mock()

        # Create test file
        test_file = tmp_path / "test.json"
        test_file.write_text(
            '{"summary": "Test", "description": "Desc", "User Story": "As a user...", "Acceptance Criteria": "* [ ] Test", "Supporting Documentation": "Docs", "Definition of Done": "Done"}'
        )

        # Mock successful response
        mock_client.request.return_value = {"key": "TEST-1"}

        args = Namespace(
            issue_type="story",
            input_dir=str(tmp_path),
            pattern="*.json",
            epic=None,
            no_ai=True,
            dry_run=False,
            output="text",
            continue_on_error=False,
        )

        with patch("builtins.print"):
            plugin.execute(mock_client, args)

        # Verify component was added to payload
        call_args = mock_client.request.call_args
        payload = call_args[1]["json_data"]
        assert "components" in payload["fields"]
        assert payload["fields"]["components"] == [{"name": "my-component"}]
        assert payload["fields"]["priority"] == {"name": "High"}

    def test_execute_without_continue_on_error_fails_fast(self, tmp_path):
        """Test batch create fails fast when continue-on-error is False."""
        plugin = BatchCreatePlugin()
        mock_client = Mock()

        # Create test files - one good, one bad
        good_file = tmp_path / "good.json"
        good_file.write_text(
            '{"summary": "Good", "description": "Desc", "User Story": "As a user...", "Acceptance Criteria": "* [ ] Test", "Supporting Documentation": "Docs", "Definition of Done": "Done"}'
        )

        bad_file = tmp_path / "bad.json"
        bad_file.write_text('{"summary": "Bad"}')  # Missing required fields

        args = Namespace(
            issue_type="story",
            input_dir=str(tmp_path),
            pattern="*.json",
            epic=None,
            no_ai=True,
            dry_run=False,
            output="text",
            continue_on_error=False,
        )

        # Should raise on first error
        with pytest.raises(BatchCreateError, match="Failed to process"):
            plugin.execute(mock_client, args)
