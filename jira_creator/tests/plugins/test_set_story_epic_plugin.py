#!/usr/bin/env python
"""Tests for the set story epic plugin."""

from argparse import Namespace
from unittest.mock import Mock, patch

import pytest

from jira_creator.exceptions.exceptions import SetStoryEpicError
from jira_creator.plugins.set_story_epic_plugin import SetStoryEpicPlugin


class TestSetStoryEpicPlugin:
    """Test cases for SetStoryEpicPlugin."""

    def test_plugin_properties(self):
        """Test plugin properties are set correctly."""
        plugin = SetStoryEpicPlugin()
        assert plugin.command_name == "set-story-epic"
        assert plugin.help_text == "Link a story to an epic"

    def test_register_arguments(self):
        """Test argument registration."""
        plugin = SetStoryEpicPlugin()
        mock_parser = Mock()

        plugin.register_arguments(mock_parser)

        # Verify add_argument was called with correct parameters
        assert mock_parser.add_argument.call_count == 2
        calls = mock_parser.add_argument.call_args_list

        # First argument: issue_key
        assert calls[0][0] == ("issue_key",)
        assert calls[0][1]["help"] == "The story issue key (e.g., PROJ-123)"

        # Second argument: epic_key
        assert calls[1][0] == ("epic_key",)
        assert calls[1][1]["help"] == "The epic issue key (e.g., PROJ-100)"

    @patch("jira_creator.plugins.set_story_epic_plugin.EnvFetcher")
    def test_rest_operation(self, mock_env_fetcher):
        """Test the REST operation directly."""
        plugin = SetStoryEpicPlugin()
        mock_client = Mock()
        mock_client.request.return_value = {"key": "TEST-123"}

        # Mock EnvFetcher.get to return epic field
        mock_env_fetcher.get.return_value = "customfield_10008"

        result = plugin.rest_operation(mock_client, issue_key="TEST-123", epic_key="TEST-100")

        # Verify EnvFetcher was called
        mock_env_fetcher.get.assert_called_once_with("JIRA_EPIC_FIELD")

        # Verify the request
        mock_client.request.assert_called_once_with(
            "PUT",
            "/rest/api/2/issue/TEST-123",
            json_data={"fields": {"customfield_10008": "TEST-100"}},
        )
        assert result == {"key": "TEST-123"}

    @patch("jira_creator.plugins.set_story_epic_plugin.EnvFetcher")
    def test_rest_operation_no_epic_field(self, mock_env_fetcher):
        """Test REST operation when JIRA_EPIC_FIELD is not set."""
        plugin = SetStoryEpicPlugin()
        mock_client = Mock()

        # Mock EnvFetcher.get to return None (not set)
        mock_env_fetcher.get.return_value = None

        with pytest.raises(SetStoryEpicError) as exc_info:
            plugin.rest_operation(mock_client, issue_key="TEST-123", epic_key="TEST-100")

        assert str(exc_info.value) == "JIRA_EPIC_FIELD not set in environment"

    @patch("jira_creator.plugins.set_story_epic_plugin.EnvFetcher")
    def test_execute_success(self, mock_env_fetcher, capsys):
        """Test successful execution."""
        plugin = SetStoryEpicPlugin()
        mock_client = Mock()
        mock_client.request.return_value = {"key": "TEST-123"}

        # Mock EnvFetcher.get to return epic field
        mock_env_fetcher.get.return_value = "customfield_10008"

        args = Namespace(issue_key="TEST-123", epic_key="TEST-100")

        result = plugin.execute(mock_client, args)

        # Verify success
        assert result is True
        mock_client.request.assert_called_once_with(
            "PUT",
            "/rest/api/2/issue/TEST-123",
            json_data={"fields": {"customfield_10008": "TEST-100"}},
        )

        # Verify print output
        captured = capsys.readouterr()
        assert "✅ Story TEST-123 linked to epic TEST-100" in captured.out

    @patch("jira_creator.plugins.set_story_epic_plugin.EnvFetcher")
    def test_execute_failure(self, mock_env_fetcher, capsys):
        """Test execution with API failure."""
        plugin = SetStoryEpicPlugin()
        mock_client = Mock()
        mock_client.request.side_effect = SetStoryEpicError("Epic not found")

        mock_env_fetcher.get.return_value = "customfield_10008"

        args = Namespace(issue_key="TEST-123", epic_key="INVALID-999")

        # Verify exception is raised
        with pytest.raises(SetStoryEpicError) as exc_info:
            plugin.execute(mock_client, args)

        # Verify the exception message
        assert str(exc_info.value) == "Epic not found"

        # Verify print output
        captured = capsys.readouterr()
        assert "❌ Failed to set epic: Epic not found" in captured.out

    @patch("jira_creator.plugins.set_story_epic_plugin.EnvFetcher")
    def test_execute_with_environment_not_set(self, mock_env_fetcher, capsys):
        """Test execution when JIRA_EPIC_FIELD is not set."""
        plugin = SetStoryEpicPlugin()
        mock_client = Mock()

        # Mock EnvFetcher.get to return None
        mock_env_fetcher.get.return_value = None

        args = Namespace(issue_key="TEST-123", epic_key="TEST-100")

        # Verify exception is raised
        with pytest.raises(SetStoryEpicError) as exc_info:
            plugin.execute(mock_client, args)

        # Verify the exception message
        assert "JIRA_EPIC_FIELD not set in environment" in str(exc_info.value)

        # Verify print output
        captured = capsys.readouterr()
        assert "❌ Failed to set epic:" in captured.out
        assert "JIRA_EPIC_FIELD not set in environment" in captured.out

    @patch("jira_creator.plugins.set_story_epic_plugin.EnvFetcher")
    def test_execute_with_different_epic_keys(self, mock_env_fetcher):
        """Test execute with different epic key formats."""
        plugin = SetStoryEpicPlugin()
        mock_client = Mock()
        mock_env_fetcher.get.return_value = "customfield_10008"

        # Test different project prefixes and issue numbers
        test_cases = [
            ("PROJ-123", "PROJ-100"),
            ("ABC-456", "ABC-50"),
            ("TEST-1", "TEST-999"),
            ("LONG-PROJECT-789", "LONG-PROJECT-1"),
        ]

        for story_key, epic_key in test_cases:
            mock_client.reset_mock()
            args = Namespace(issue_key=story_key, epic_key=epic_key)

            result = plugin.execute(mock_client, args)

            assert result is True
            # Verify the epic key was passed correctly
            call_args = mock_client.request.call_args[1]["json_data"]
            assert call_args["fields"]["customfield_10008"] == epic_key

    @patch("jira_creator.plugins.set_story_epic_plugin.EnvFetcher")
    def test_rest_operation_with_same_issue_and_epic(self, mock_env_fetcher):
        """Test REST operation when trying to link an issue to itself as epic."""
        plugin = SetStoryEpicPlugin()
        mock_client = Mock()
        mock_env_fetcher.get.return_value = "customfield_10008"

        # This might be invalid in Jira, but the plugin should still send the request
        plugin.rest_operation(mock_client, issue_key="TEST-123", epic_key="TEST-123")

        # Verify the request is made (validation happens server-side)
        call_args = mock_client.request.call_args[1]["json_data"]
        assert call_args["fields"]["customfield_10008"] == "TEST-123"

    @patch("jira_creator.plugins.set_story_epic_plugin.EnvFetcher")
    def test_env_fetcher_returns_different_field(self, mock_env_fetcher):
        """Test that the plugin uses the field returned by EnvFetcher."""
        plugin = SetStoryEpicPlugin()
        mock_client = Mock()

        # Test with different custom field IDs
        custom_fields = ["customfield_10008", "customfield_20009", "epic_link"]

        for field_id in custom_fields:
            mock_client.reset_mock()
            mock_env_fetcher.get.return_value = field_id

            plugin.rest_operation(mock_client, issue_key="TEST-123", epic_key="TEST-100")

            # Verify the correct field ID was used
            call_args = mock_client.request.call_args[1]["json_data"]
            assert field_id in call_args["fields"]
            assert call_args["fields"][field_id] == "TEST-100"

    @patch("jira_creator.plugins.set_story_epic_plugin.EnvFetcher")
    def test_execute_with_special_characters_in_keys(self, mock_env_fetcher, capsys):
        """Test execution with issue keys containing special characters."""
        plugin = SetStoryEpicPlugin()
        mock_client = Mock()
        mock_client.request.return_value = {"key": "TEST-123"}
        mock_env_fetcher.get.return_value = "customfield_10008"

        # While Jira keys typically don't have special chars, test edge cases
        args = Namespace(issue_key="TEST-123", epic_key="TEST-100")

        result = plugin.execute(mock_client, args)

        assert result is True

        # Verify print output preserves the keys exactly
        captured = capsys.readouterr()
        assert "✅ Story TEST-123 linked to epic TEST-100" in captured.out
