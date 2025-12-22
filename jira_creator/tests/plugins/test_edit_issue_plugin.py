#!/usr/bin/env python
"""Tests for the edit issue plugin."""

from argparse import ArgumentParser, Namespace
from unittest.mock import Mock, patch

import pytest

from jira_creator.core.env_fetcher import EnvFetcher
from jira_creator.plugins.edit_issue_plugin import (
    EditDescriptionError,
    EditIssueError,
    EditIssuePlugin,
    FetchDescriptionError,
)

# Add logging environment variables to EnvFetcher vars for testing BEFORE importing the plugin
if not hasattr(EnvFetcher, "vars"):
    EnvFetcher.vars = {}

for var in ["JIRA_LOG_LEVEL", "JIRA_LOG_FILE", "JIRA_LOG_FORMAT", "JIRA_ACCEPTANCE_CRITERIA_FIELD"]:
    if var not in EnvFetcher.vars:
        EnvFetcher.vars[var] = ""


class TestEditIssuePlugin:
    """Test cases for EditIssuePlugin."""

    def test_plugin_properties(self):
        """Test plugin properties are set correctly."""
        plugin = EditIssuePlugin()
        assert plugin.command_name == "edit-issue"
        assert plugin.help_text == "Edit a Jira issue description"

    def test_register_arguments(self):
        """Test argument registration."""
        plugin = EditIssuePlugin()
        mock_parser = Mock(spec=ArgumentParser)

        plugin.register_arguments(mock_parser)

        # Check all arguments are registered (5 total: issue_key, --no-ai, --lint, --acceptance-criteria, --ai-from-description)
        assert mock_parser.add_argument.call_count == 5

    def test_rest_operation(self):
        """Test the REST operation directly."""
        plugin = EditIssuePlugin()
        mock_client = Mock()
        mock_response = {"id": "10001", "key": "TEST-123"}
        mock_client.request.return_value = mock_response

        result = plugin.rest_operation(mock_client, issue_key="TEST-123", description="Updated description")

        expected_payload = {"fields": {"description": "Updated description"}}
        mock_client.request.assert_called_once_with("PUT", "/rest/api/2/issue/TEST-123", json_data=expected_payload)
        assert result == mock_response

    def test_execute_successful_with_changes(self):
        """Test successful execution when description is changed."""

        # Mock editor function
        def mock_editor(cmd_list):
            filename = cmd_list[1]
            with open(filename, "w") as f:
                f.write("Edited description")

        plugin = EditIssuePlugin(editor_func=mock_editor)
        mock_client = Mock()

        # Mock fetch description response
        mock_client.request.side_effect = [
            # First call: fetch description
            {"fields": {"description": "Original description"}},
            # Second call: get issue type
            {"fields": {"issuetype": {"name": "Story"}}},
            # Third call: update description
            {},
        ]

        args = Namespace(
            acceptance_criteria=False, ai_from_description=False, issue_key="TEST-123", no_ai=True, lint=False
        )

        with patch("builtins.print") as mock_print:
            result = plugin.execute(mock_client, args)

        assert result is True

        # Check messages
        print_calls = [call[0][0] for call in mock_print.call_args_list]
        assert any("📥 Fetching description for TEST-123" in str(call) for call in print_calls)
        assert any("📝 Opening editor" in str(call) for call in print_calls)
        assert any("✅ Successfully updated description for TEST-123" in str(call) for call in print_calls)

    def test_execute_no_changes_made(self):
        """Test execution when no changes are made to description."""

        # Mock editor function that doesn't change content
        def mock_editor(cmd_list):
            filename = cmd_list[1]
            # Read the content and write it back unchanged
            with open(filename, "r") as f:
                content = f.read()
            with open(filename, "w") as f:
                f.write(content)

        plugin = EditIssuePlugin(editor_func=mock_editor)
        mock_client = Mock()

        # Mock fetch description response
        mock_client.request.return_value = {"fields": {"description": "Original description"}}

        args = Namespace(
            acceptance_criteria=False, ai_from_description=False, issue_key="TEST-123", no_ai=True, lint=False
        )

        with patch("builtins.print") as mock_print:
            result = plugin.execute(mock_client, args)

        assert result is True

        # Should only have 2 API calls (fetch and issue type), not update
        assert mock_client.request.call_count == 1

        # Check no changes message
        print_calls = [call[0][0] for call in mock_print.call_args_list]
        assert any("ℹ️  No changes made to description" in str(call) for call in print_calls)

    def test_execute_with_ai_enhancement(self):
        """Test execution with AI enhancement enabled."""
        # Mock AI provider
        mock_ai = Mock()
        mock_ai.improve_text.return_value = "AI enhanced description"

        # Mock editor
        def mock_editor(cmd_list):
            filename = cmd_list[1]
            with open(filename, "w") as f:
                f.write("Edited description")

        plugin = EditIssuePlugin(ai_provider=mock_ai, editor_func=mock_editor)
        mock_client = Mock()

        # Mock API responses
        mock_client.request.side_effect = [
            # Fetch description
            {"fields": {"description": "Original"}},
            # Get issue type
            {"fields": {"issuetype": {"name": "Bug"}}},
            # Update description
            {},
        ]

        args = Namespace(
            acceptance_criteria=False, ai_from_description=False, issue_key="TEST-456", no_ai=False, lint=False
        )

        with patch("builtins.print") as mock_print:
            result = plugin.execute(mock_client, args)

        assert result is True
        mock_ai.improve_text.assert_called_once()

        # Verify AI enhanced description was used
        update_call = mock_client.request.call_args_list[2]
        assert update_call[1]["json_data"]["fields"]["description"] == "AI enhanced description"

        # Check AI message
        print_calls = [call[0][0] for call in mock_print.call_args_list]
        assert any("🤖 Enhancing description with AI" in str(call) for call in print_calls)

    def test_execute_with_ai_error(self):
        """Test execution when AI enhancement fails."""
        # Mock AI provider that fails
        mock_ai = Mock()
        mock_ai.improve_text.side_effect = Exception("AI service error")

        # Mock editor
        def mock_editor(cmd_list):
            filename = cmd_list[1]
            with open(filename, "w") as f:
                f.write("Edited description")

        plugin = EditIssuePlugin(ai_provider=mock_ai, editor_func=mock_editor)
        mock_client = Mock()

        # Mock API responses
        mock_client.request.side_effect = [
            {"fields": {"description": "Original"}},
            {"fields": {"issuetype": {"name": "Story"}}},
            {},
        ]

        args = Namespace(
            acceptance_criteria=False, ai_from_description=False, issue_key="TEST-789", no_ai=False, lint=False
        )

        with patch("builtins.print") as mock_print:
            result = plugin.execute(mock_client, args)

        assert result is True

        # Check AI error message
        print_calls = [call[0][0] for call in mock_print.call_args_list]
        assert any("⚠️  AI enhancement failed, using edited text" in str(call) for call in print_calls)

        # Verify edited description was used (not AI enhanced)
        update_call = mock_client.request.call_args_list[2]
        assert update_call[1]["json_data"]["fields"]["description"] == "Edited description"

    def test_execute_with_lint(self):
        """Test execution with linting enabled."""

        # Mock editor
        def mock_editor(cmd_list):
            filename = cmd_list[1]
            with open(filename, "w") as f:
                f.write("Description to lint")

        plugin = EditIssuePlugin(editor_func=mock_editor)
        mock_client = Mock()

        mock_client.request.side_effect = [{"fields": {"description": "Original"}}, {}]

        args = Namespace(
            acceptance_criteria=False, ai_from_description=False, issue_key="TEST-321", no_ai=True, lint=True
        )

        with patch("builtins.print") as mock_print:
            result = plugin.execute(mock_client, args)

        assert result is True

        # Check lint messages
        print_calls = [call[0][0] for call in mock_print.call_args_list]
        assert any("🔍 Linting description" in str(call) for call in print_calls)
        assert any("ℹ️  Interactive linting not fully implemented" in str(call) for call in print_calls)

    def test_execute_with_error(self):
        """Test execution when update fails."""

        # Mock editor function
        def mock_editor(cmd_list):
            filename = cmd_list[1]
            with open(filename, "w") as f:
                f.write("Edited description")

        plugin = EditIssuePlugin(editor_func=mock_editor)
        mock_client = Mock()

        # Make update fail
        mock_client.request.side_effect = [
            {"fields": {"description": "Original"}},
            EditIssueError("Update failed"),
        ]

        args = Namespace(
            acceptance_criteria=False, ai_from_description=False, issue_key="TEST-999", no_ai=True, lint=False
        )

        with patch("builtins.print") as mock_print:
            with pytest.raises(EditIssueError):
                plugin.execute(mock_client, args)

        # Check error message
        print_calls = [call[0][0] for call in mock_print.call_args_list]
        assert any("❌ Failed to edit issue" in str(call) for call in print_calls)

    def test_fetch_description_success(self):
        """Test fetching description successfully."""
        plugin = EditIssuePlugin()
        mock_client = Mock()
        mock_client.request.return_value = {"fields": {"description": "Test description"}}

        result = plugin._fetch_description(mock_client, "TEST-123")

        assert result == "Test description"
        mock_client.request.assert_called_once_with("GET", "/rest/api/2/issue/TEST-123?fields=description")

    def test_fetch_description_empty(self):
        """Test fetching description when issue has no description."""
        plugin = EditIssuePlugin()
        mock_client = Mock()
        mock_client.request.return_value = {"fields": {"description": ""}}

        with pytest.raises(FetchDescriptionError, match="Issue has no description"):
            plugin._fetch_description(mock_client, "TEST-123")

    def test_fetch_description_error(self):
        """Test fetching description when API call fails."""
        plugin = EditIssuePlugin()
        mock_client = Mock()
        mock_client.request.side_effect = Exception("API error")

        with pytest.raises(FetchDescriptionError, match="Failed to fetch description"):
            plugin._fetch_description(mock_client, "TEST-123")

    def test_get_issue_type_success(self):
        """Test getting issue type successfully."""
        plugin = EditIssuePlugin()
        mock_client = Mock()
        mock_client.request.return_value = {"fields": {"issuetype": {"name": "Bug"}}}

        result = plugin._get_issue_type(mock_client, "TEST-123")

        assert result == "BUG"
        mock_client.request.assert_called_once_with("GET", "/rest/api/2/issue/TEST-123?fields=issuetype")

    def test_get_issue_type_failure(self):
        """Test getting issue type when it fails (returns default)."""
        plugin = EditIssuePlugin()
        mock_client = Mock()
        mock_client.request.side_effect = Exception("API error")

        result = plugin._get_issue_type(mock_client, "TEST-123")

        assert result == "STORY"  # Default value

    def test_edit_text_empty(self):
        """Test editing description when user clears it."""

        # Mock editor that clears content
        def mock_editor(cmd_list):
            filename = cmd_list[1]
            with open(filename, "w") as f:
                f.write("   ")  # Only whitespace

        plugin = EditIssuePlugin(editor_func=mock_editor)

        with pytest.raises(EditDescriptionError, match="Edited text cannot be empty"):
            plugin._edit_text("Original content")

    @patch("os.environ.get")
    def test_edit_text_custom_editor(self, mock_env_get):
        """Test editing description with custom editor from environment."""
        mock_env_get.return_value = "emacs"

        mock_editor = Mock()
        plugin = EditIssuePlugin(editor_func=mock_editor)

        with patch("tempfile.NamedTemporaryFile") as mock_temp:
            mock_file = Mock()
            mock_file.name = "/tmp/test.md"
            mock_file.read.return_value = "Edited content"
            mock_temp.return_value.__enter__.return_value = mock_file

            plugin._edit_text("Original")

        # Verify custom editor was used
        mock_editor.assert_called_once()
        call_args = mock_editor.call_args[0][0]
        assert call_args[0] == "emacs"

    @patch("jira_creator.plugins.edit_issue_plugin.get_ai_provider")
    @patch("jira_creator.plugins.edit_issue_plugin.EnvFetcher")
    def test_enhance_with_ai_all_issue_types(self, mock_env_fetcher, mock_get_ai_provider):
        """Test AI enhancement with all issue types."""
        mock_env_fetcher.get.return_value = "openai"

        mock_ai = Mock()
        mock_ai.improve_text.return_value = "Enhanced text"
        mock_get_ai_provider.return_value = mock_ai

        plugin = EditIssuePlugin()

        # Test valid issue types
        for issue_type in ["STORY", "BUG", "EPIC", "TASK", "SPIKE"]:
            result = plugin._enhance_with_ai("Original", issue_type)
            assert result == "Enhanced text"

        # Test invalid issue type (should default to STORY)
        result = plugin._enhance_with_ai("Original", "INVALID")
        assert result == "Enhanced text"

    def test_lint_description(self):
        """Test linting description (simplified version)."""
        plugin = EditIssuePlugin()

        with patch("builtins.print") as mock_print:
            result = plugin._lint_description("Test description")

        assert result == "Test description"  # Returns unchanged

        # Check lint messages
        print_calls = [call[0][0] for call in mock_print.call_args_list]
        assert any("🔍 Linting description" in str(call) for call in print_calls)
        assert any("ℹ️  Interactive linting not fully implemented" in str(call) for call in print_calls)

    def test_dependency_injection(self):
        """Test dependency injection mechanism."""
        # Test with injected dependencies
        mock_ai = Mock()
        mock_editor = Mock()

        plugin = EditIssuePlugin(ai_provider=mock_ai, editor_func=mock_editor)

        assert plugin.get_dependency("ai_provider") == mock_ai
        assert plugin.get_dependency("editor_func") == mock_editor
        assert plugin.get_dependency("nonexistent", "default") == "default"

    @patch("jira_creator.plugins.edit_issue_plugin.subprocess.call")
    def test_edit_text_default_behavior(self, mock_subprocess):
        """Test edit description with default subprocess behavior."""
        plugin = EditIssuePlugin()

        with patch("tempfile.NamedTemporaryFile") as mock_temp:
            mock_file = Mock()
            mock_file.name = "/tmp/test.md"
            mock_file.read.return_value = "Edited content"
            mock_temp.return_value.__enter__.return_value = mock_file

            result = plugin._edit_text("Original content")

        assert result == "Edited content"
        mock_subprocess.assert_called_once()

    def test_execute_with_multiple_api_calls(self):
        """Test execution with multiple API calls to ensure proper sequencing."""
        plugin = EditIssuePlugin()
        mock_client = Mock()

        # Track API call sequence
        api_calls = []

        def track_calls(method, path, **kwargs):
            api_calls.append((method, path))
            if "fields=description" in path:
                return {"fields": {"description": "Original"}}
            elif "fields=issuetype" in path:
                return {"fields": {"issuetype": {"name": "Epic"}}}
            else:
                return {}

        mock_client.request.side_effect = track_calls

        args = Namespace(
            acceptance_criteria=False, ai_from_description=False, issue_key="TEST-100", no_ai=True, lint=False
        )

        with patch("builtins.print"):
            # Mock editor to make a change
            with patch.object(plugin, "_edit_text", return_value="Changed"):
                plugin.execute(mock_client, args)

        # Verify API call sequence (only 2 calls when no_ai=True)
        assert len(api_calls) == 2
        assert api_calls[0] == ("GET", "/rest/api/2/issue/TEST-100?fields=description")
        assert api_calls[1] == ("PUT", "/rest/api/2/issue/TEST-100")

    def test_execute_fetch_description_none(self):
        """Test execution when description field is None."""
        plugin = EditIssuePlugin()
        mock_client = Mock()

        # Return None for description field
        mock_client.request.return_value = {"fields": {"description": None}}

        args = Namespace(
            acceptance_criteria=False, ai_from_description=False, issue_key="TEST-NULL", no_ai=True, lint=False
        )

        with patch("builtins.print"):
            with pytest.raises(FetchDescriptionError, match="Issue has no description"):
                plugin.execute(mock_client, args)

    @patch("jira_creator.plugins.edit_issue_plugin.EnvFetcher")
    def test_execute_with_acceptance_criteria_flag_requires_no_ai_from_desc(self, mock_env):
        """Test that --ai-from-description requires --acceptance-criteria."""
        plugin = EditIssuePlugin()
        mock_client = Mock()
        mock_env.get.return_value = "customfield_10050"

        args = Namespace(
            acceptance_criteria=False, ai_from_description=True, issue_key="TEST-123", no_ai=True, lint=False
        )

        with patch("builtins.print") as mock_print:
            result = plugin.execute(mock_client, args)

        assert result is False
        print_calls = [call[0][0] for call in mock_print.call_args_list]
        assert any("--ai-from-description requires --acceptance-criteria" in str(call) for call in print_calls)

    @patch("jira_creator.plugins.edit_issue_plugin.EnvFetcher")
    def test_edit_acceptance_criteria_manual(self, mock_env):
        """Test manually editing acceptance criteria."""
        mock_env.get.return_value = "customfield_10050"

        # Mock editor function
        def mock_editor(cmd_list):
            filename = cmd_list[1]
            with open(filename, "w") as f:
                f.write("* [ ] New criteria")

        plugin = EditIssuePlugin(editor_func=mock_editor)
        mock_client = Mock()

        # Mock API responses
        mock_client.request.side_effect = [
            # Fetch current AC
            {"fields": {"customfield_10050": "* [ ] Old criteria"}},
            # Update AC
            {},
        ]

        args = Namespace(
            acceptance_criteria=True, ai_from_description=False, issue_key="TEST-123", no_ai=True, lint=False
        )

        with patch("builtins.print") as mock_print:
            result = plugin.execute(mock_client, args)

        assert result is True
        print_calls = [call[0][0] for call in mock_print.call_args_list]
        assert any("Successfully updated acceptance criteria" in str(call) for call in print_calls)

    @patch("jira_creator.plugins.edit_issue_plugin.EnvFetcher")
    def test_edit_acceptance_criteria_no_changes(self, mock_env):
        """Test editing AC when no changes are made."""
        mock_env.get.return_value = "customfield_10050"

        # Mock editor function that doesn't change content
        def mock_editor(cmd_list):
            filename = cmd_list[1]
            # Read and write back unchanged
            with open(filename, "r") as f:
                content = f.read()
            with open(filename, "w") as f:
                f.write(content)

        plugin = EditIssuePlugin(editor_func=mock_editor)
        mock_client = Mock()

        # Mock API response
        mock_client.request.return_value = {"fields": {"customfield_10050": "Unchanged"}}

        args = Namespace(
            acceptance_criteria=True, ai_from_description=False, issue_key="TEST-123", no_ai=True, lint=False
        )

        with patch("builtins.print") as mock_print:
            result = plugin.execute(mock_client, args)

        assert result is True
        print_calls = [call[0][0] for call in mock_print.call_args_list]
        assert any("No changes made to acceptance criteria" in str(call) for call in print_calls)

    @patch("jira_creator.plugins.edit_issue_plugin.get_ai_provider")
    @patch("jira_creator.plugins.edit_issue_plugin.EnvFetcher")
    def test_edit_acceptance_criteria_ai_from_description(self, mock_env, mock_get_ai):
        """Test generating AC from description using AI."""
        mock_env.get.side_effect = lambda key, default="": {
            "JIRA_ACCEPTANCE_CRITERIA_FIELD": "customfield_10050",
            "JIRA_AI_PROVIDER": "openai",
        }.get(key, default)

        mock_ai = Mock()
        mock_ai.complete.return_value = "* [ ] AI generated criteria"
        mock_get_ai.return_value = mock_ai

        plugin = EditIssuePlugin()
        mock_client = Mock()

        # Mock API responses
        mock_client.request.side_effect = [
            # Fetch issue for description
            {"fields": {"description": "User wants to login", "summary": "Login feature"}},
            # Update AC
            {},
        ]

        args = Namespace(
            acceptance_criteria=True, ai_from_description=True, issue_key="TEST-123", no_ai=True, lint=False
        )

        with patch("builtins.print") as mock_print:
            result = plugin.execute(mock_client, args)

        assert result is True
        mock_ai.complete.assert_called_once()
        print_calls = [call[0][0] for call in mock_print.call_args_list]
        assert any("Generating acceptance criteria from description" in str(call) for call in print_calls)

    @patch("jira_creator.plugins.edit_issue_plugin.EnvFetcher")
    def test_fetch_acceptance_criteria_empty(self, mock_env):
        """Test fetching empty acceptance criteria."""
        mock_env.get.return_value = "customfield_10050"

        plugin = EditIssuePlugin()
        mock_client = Mock()
        mock_client.request.return_value = {"fields": {"customfield_10050": ""}}

        result = plugin._fetch_acceptance_criteria(mock_client, "TEST-123")

        assert result == ""

    @patch("jira_creator.plugins.edit_issue_plugin.EnvFetcher")
    def test_fetch_acceptance_criteria_none(self, mock_env):
        """Test fetching None acceptance criteria."""
        mock_env.get.return_value = "customfield_10050"

        plugin = EditIssuePlugin()
        mock_client = Mock()
        mock_client.request.return_value = {"fields": {"customfield_10050": None}}

        result = plugin._fetch_acceptance_criteria(mock_client, "TEST-123")

        assert result == ""

    @patch("jira_creator.plugins.edit_issue_plugin.EnvFetcher")
    def test_fetch_acceptance_criteria_error(self, mock_env):
        """Test fetching AC when API fails."""
        mock_env.get.return_value = "customfield_10050"

        plugin = EditIssuePlugin()
        mock_client = Mock()
        mock_client.request.side_effect = Exception("API Error")

        result = plugin._fetch_acceptance_criteria(mock_client, "TEST-123")

        assert result == ""

    @patch("jira_creator.plugins.edit_issue_plugin.get_ai_provider")
    @patch("jira_creator.plugins.edit_issue_plugin.EnvFetcher")
    def test_generate_ac_from_description_no_description(self, mock_env, mock_get_ai):
        """Test generating AC when issue has no description."""
        mock_env.get.return_value = "openai"

        plugin = EditIssuePlugin()
        mock_client = Mock()
        mock_client.request.return_value = {"fields": {"description": "", "summary": "Test"}}

        with pytest.raises(EditIssueError, match="has no description to generate from"):
            plugin._generate_ac_from_description(mock_client, "TEST-123")

    @patch("jira_creator.plugins.edit_issue_plugin.get_ai_provider")
    @patch("jira_creator.plugins.edit_issue_plugin.EnvFetcher")
    def test_generate_ac_from_description_ai_empty(self, mock_env, mock_get_ai):
        """Test generating AC when AI returns empty."""
        mock_env.get.return_value = "openai"

        mock_ai = Mock()
        mock_ai.complete.return_value = "   "
        mock_get_ai.return_value = mock_ai

        plugin = EditIssuePlugin()
        mock_client = Mock()
        mock_client.request.return_value = {"fields": {"description": "Test", "summary": "Test"}}

        with pytest.raises(EditIssueError, match="AI generated empty acceptance criteria"):
            plugin._generate_ac_from_description(mock_client, "TEST-123")

    @patch("jira_creator.plugins.edit_issue_plugin.get_ai_provider")
    @patch("jira_creator.plugins.edit_issue_plugin.EnvFetcher")
    def test_generate_ac_from_description_ai_error(self, mock_env, mock_get_ai):
        """Test generating AC when AI fails."""
        mock_env.get.return_value = "openai"

        mock_get_ai.side_effect = Exception("AI service down")

        plugin = EditIssuePlugin()
        mock_client = Mock()
        mock_client.request.return_value = {"fields": {"description": "Test", "summary": "Test"}}

        with pytest.raises(EditIssueError, match="Failed to generate acceptance criteria"):
            plugin._generate_ac_from_description(mock_client, "TEST-123")

    @patch("jira_creator.plugins.edit_issue_plugin.EnvFetcher")
    def test_update_acceptance_criteria_error(self, mock_env):
        """Test updating AC when API fails."""
        mock_env.get.return_value = "customfield_10050"

        plugin = EditIssuePlugin()
        mock_client = Mock()
        mock_client.request.side_effect = Exception("Update failed")

        with pytest.raises(EditIssueError, match="Failed to update acceptance criteria"):
            plugin._update_acceptance_criteria(mock_client, "TEST-123", "New criteria")
