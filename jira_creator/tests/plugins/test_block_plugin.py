#!/usr/bin/env python
"""Tests for the block plugin."""

from argparse import Namespace
from unittest.mock import Mock, patch

import pytest

from jira_creator.exceptions.exceptions import BlockError
from jira_creator.plugins.block_plugin import BlockPlugin


class TestBlockPlugin:
    """Test cases for BlockPlugin."""

    def test_plugin_properties(self):
        """Test plugin properties are set correctly."""
        plugin = BlockPlugin()
        assert plugin.command_name == "block"
        assert plugin.help_text == "Mark a Jira issue as blocked"

    def test_register_arguments(self):
        """Test argument registration."""
        plugin = BlockPlugin()
        mock_parser = Mock()

        plugin.register_arguments(mock_parser)

        assert mock_parser.add_argument.call_count == 2
        calls = mock_parser.add_argument.call_args_list

        # Check issue_key argument
        assert calls[0][0][0] == "issue_key"
        assert calls[0][1]["help"] == "The Jira issue key (e.g., PROJ-123)"

        # Check reason argument
        assert calls[1][0][0] == "reason"
        assert calls[1][1]["nargs"] == "+"
        assert calls[1][1]["help"] == "The reason for blocking the issue"

    @patch("jira_creator.plugins.block_plugin.EnvFetcher.get")
    def test_rest_operation(self, mock_env_get):
        """Test the REST operation for blocking an issue."""
        plugin = BlockPlugin()
        mock_client = Mock()

        # Mock environment variables
        mock_env_get.side_effect = lambda key: {
            "JIRA_BLOCKED_FIELD": "customfield_10001",
            "JIRA_BLOCKED_REASON_FIELD": "customfield_10002",
        }.get(key)

        result = plugin.rest_operation(
            mock_client,
            issue_key="TEST-123",
            reason="Waiting for external dependencies",
        )

        # Verify the correct API call was made
        mock_client.request.assert_called_once_with(
            "PUT",
            "/rest/api/2/issue/TEST-123",
            json_data={
                "fields": {
                    "customfield_10001": {"id": "14656"},
                    "customfield_10002": "Waiting for external dependencies",
                }
            },
        )
        assert result == mock_client.request.return_value

    def test_execute_success(self):
        """Test successful execution of block command."""
        plugin = BlockPlugin()
        mock_client = Mock()

        args = Namespace(issue_key="TEST-123", reason=["Waiting", "for", "dependencies"])

        with patch("jira_creator.plugins.block_plugin.EnvFetcher.get") as mock_env:
            mock_env.side_effect = lambda key: {
                "JIRA_BLOCKED_FIELD": "customfield_10001",
                "JIRA_BLOCKED_REASON_FIELD": "customfield_10002",
            }.get(key)

            result = plugin.execute(mock_client, args)

        assert result is True
        mock_client.request.assert_called_once()

    def test_execute_success_prints_message(self, capsys):
        """Test that success message is printed."""
        plugin = BlockPlugin()
        mock_client = Mock()

        args = Namespace(issue_key="TEST-123", reason=["Waiting", "for", "dependencies"])

        with patch("jira_creator.plugins.block_plugin.EnvFetcher.get") as mock_env:
            mock_env.side_effect = lambda key: {
                "JIRA_BLOCKED_FIELD": "customfield_10001",
                "JIRA_BLOCKED_REASON_FIELD": "customfield_10002",
            }.get(key)

            plugin.execute(mock_client, args)

        captured = capsys.readouterr()
        assert "✅ TEST-123 marked as blocked: Waiting for dependencies" in captured.out

    def test_execute_joins_reason_words(self):
        """Test that reason words are joined correctly."""
        plugin = BlockPlugin()
        mock_client = Mock()

        args = Namespace(issue_key="TEST-123", reason=["This", "is", "a", "multi-word", "reason"])

        with patch("jira_creator.plugins.block_plugin.EnvFetcher.get") as mock_env:
            mock_env.side_effect = lambda key: {
                "JIRA_BLOCKED_FIELD": "customfield_10001",
                "JIRA_BLOCKED_REASON_FIELD": "customfield_10002",
            }.get(key)

            plugin.execute(mock_client, args)

        # Check that the reason was joined properly
        call_args = mock_client.request.call_args
        assert call_args[1]["json_data"]["fields"]["customfield_10002"] == "This is a multi-word reason"

    def test_execute_failure(self):
        """Test handling of BlockError during execution."""
        plugin = BlockPlugin()
        mock_client = Mock()
        mock_client.request.side_effect = BlockError("Field not found")

        args = Namespace(issue_key="TEST-123", reason=["Test", "reason"])

        with patch("jira_creator.plugins.block_plugin.EnvFetcher.get") as mock_env:
            mock_env.side_effect = lambda key: {
                "JIRA_BLOCKED_FIELD": "customfield_10001",
                "JIRA_BLOCKED_REASON_FIELD": "customfield_10002",
            }.get(key)

            with pytest.raises(BlockError) as exc_info:
                plugin.execute(mock_client, args)

        assert "Field not found" in str(exc_info.value)

    def test_execute_failure_prints_message(self, capsys):
        """Test that error message is printed on failure."""
        plugin = BlockPlugin()
        mock_client = Mock()
        mock_client.request.side_effect = BlockError("Permission denied")

        args = Namespace(issue_key="TEST-123", reason=["Test"])

        with patch("jira_creator.plugins.block_plugin.EnvFetcher.get") as mock_env:
            mock_env.side_effect = lambda key: {
                "JIRA_BLOCKED_FIELD": "customfield_10001",
                "JIRA_BLOCKED_REASON_FIELD": "customfield_10002",
            }.get(key)

            with pytest.raises(BlockError):
                plugin.execute(mock_client, args)

        captured = capsys.readouterr()
        assert "❌ Failed to mark TEST-123 as blocked: Permission denied" in captured.out

    @patch("jira_creator.plugins.block_plugin.EnvFetcher.get")
    def test_rest_operation_uses_env_fields(self, mock_env_get):
        """Test that REST operation uses field IDs from environment."""
        plugin = BlockPlugin()
        mock_client = Mock()

        # Test with different field IDs
        mock_env_get.side_effect = lambda key: {
            "JIRA_BLOCKED_FIELD": "customfield_99999",
            "JIRA_BLOCKED_REASON_FIELD": "customfield_88888",
        }.get(key)

        plugin.rest_operation(mock_client, issue_key="TEST-456", reason="Different reason")

        # Verify the custom field IDs were used
        call_args = mock_client.request.call_args
        fields = call_args[1]["json_data"]["fields"]
        assert "customfield_99999" in fields
        assert "customfield_88888" in fields
        assert fields["customfield_99999"] == {"id": "14656"}
        assert fields["customfield_88888"] == "Different reason"
