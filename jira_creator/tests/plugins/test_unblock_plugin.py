#!/usr/bin/env python
"""Tests for the unblock plugin."""

from argparse import Namespace
from unittest.mock import Mock, patch

import pytest

from jira_creator.exceptions.exceptions import UnBlockError
from jira_creator.plugins.unblock_plugin import UnblockPlugin


class TestUnblockPlugin:
    """Test cases for UnblockPlugin."""

    def test_plugin_properties(self):
        """Test plugin properties are set correctly."""
        plugin = UnblockPlugin()
        assert plugin.command_name == "unblock"
        assert plugin.help_text == "Remove the blocked status from a Jira issue"

    def test_register_arguments(self):
        """Test argument registration."""
        plugin = UnblockPlugin()
        mock_parser = Mock()

        plugin.register_arguments(mock_parser)

        mock_parser.add_argument.assert_called_once_with("issue_key", help="The Jira issue key (e.g., PROJ-123)")

    @patch("jira_creator.plugins.unblock_plugin.EnvFetcher")
    def test_rest_operation(self, mock_env_fetcher):
        """Test the REST operation for unblocking an issue."""
        # Mock environment variables
        mock_env_fetcher.get.side_effect = lambda key: {
            "JIRA_BLOCKED_FIELD": "customfield_10000",
            "JIRA_BLOCKED_REASON_FIELD": "customfield_10001",
        }.get(key)

        plugin = UnblockPlugin()
        mock_client = Mock()

        result = plugin.rest_operation(mock_client, issue_key="TEST-123")

        # Verify environment variables were fetched
        assert mock_env_fetcher.get.call_count == 2
        mock_env_fetcher.get.assert_any_call("JIRA_BLOCKED_FIELD")
        mock_env_fetcher.get.assert_any_call("JIRA_BLOCKED_REASON_FIELD")

        # Verify the correct API call was made
        mock_client.request.assert_called_once_with(
            "PUT",
            "/rest/api/2/issue/TEST-123",
            json_data={
                "fields": {
                    "customfield_10000": {"value": False},
                    "customfield_10001": "",
                }
            },
        )
        assert result == mock_client.request.return_value

    @patch("jira_creator.plugins.unblock_plugin.EnvFetcher")
    def test_execute_success(self, mock_env_fetcher):
        """Test successful execution of unblock command."""
        mock_env_fetcher.get.side_effect = lambda key: {
            "JIRA_BLOCKED_FIELD": "customfield_10000",
            "JIRA_BLOCKED_REASON_FIELD": "customfield_10001",
        }.get(key)

        plugin = UnblockPlugin()
        mock_client = Mock()

        args = Namespace(issue_key="TEST-123")

        result = plugin.execute(mock_client, args)

        assert result is True
        mock_client.request.assert_called_once()

    @patch("jira_creator.plugins.unblock_plugin.EnvFetcher")
    def test_execute_success_prints_message(self, mock_env_fetcher, capsys):
        """Test that success message is printed."""
        mock_env_fetcher.get.side_effect = lambda key: {
            "JIRA_BLOCKED_FIELD": "customfield_10000",
            "JIRA_BLOCKED_REASON_FIELD": "customfield_10001",
        }.get(key)

        plugin = UnblockPlugin()
        mock_client = Mock()

        args = Namespace(issue_key="TEST-123")

        plugin.execute(mock_client, args)

        captured = capsys.readouterr()
        assert "✅ TEST-123 marked as unblocked" in captured.out

    @patch("jira_creator.plugins.unblock_plugin.EnvFetcher")
    def test_execute_failure(self, mock_env_fetcher):
        """Test handling of UnBlockError during execution."""
        mock_env_fetcher.get.side_effect = lambda key: {
            "JIRA_BLOCKED_FIELD": "customfield_10000",
            "JIRA_BLOCKED_REASON_FIELD": "customfield_10001",
        }.get(key)

        plugin = UnblockPlugin()
        mock_client = Mock()
        mock_client.request.side_effect = UnBlockError("Issue not found")

        args = Namespace(issue_key="TEST-123")

        with pytest.raises(UnBlockError) as exc_info:
            plugin.execute(mock_client, args)

        assert "Issue not found" in str(exc_info.value)

    @patch("jira_creator.plugins.unblock_plugin.EnvFetcher")
    def test_execute_failure_prints_message(self, mock_env_fetcher, capsys):
        """Test that error message is printed on failure."""
        mock_env_fetcher.get.side_effect = lambda key: {
            "JIRA_BLOCKED_FIELD": "customfield_10000",
            "JIRA_BLOCKED_REASON_FIELD": "customfield_10001",
        }.get(key)

        plugin = UnblockPlugin()
        mock_client = Mock()
        mock_client.request.side_effect = UnBlockError("Permission denied")

        args = Namespace(issue_key="TEST-123")

        with pytest.raises(UnBlockError):
            plugin.execute(mock_client, args)

        captured = capsys.readouterr()
        assert "❌ Failed to unblock TEST-123: Permission denied" in captured.out

    @patch("jira_creator.plugins.unblock_plugin.EnvFetcher")
    def test_execute_with_different_issue_keys(self, mock_env_fetcher):
        """Test execution with various issue key formats."""
        mock_env_fetcher.get.side_effect = lambda key: {
            "JIRA_BLOCKED_FIELD": "customfield_10000",
            "JIRA_BLOCKED_REASON_FIELD": "customfield_10001",
        }.get(key)

        plugin = UnblockPlugin()
        mock_client = Mock()

        # Test with different issue key formats
        test_cases = [
            "PROJ-123",
            "ABC-1",
            "LONGPROJECT-99999",
            "X-1234",
        ]

        for issue_key in test_cases:
            mock_client.reset_mock()
            args = Namespace(issue_key=issue_key)

            result = plugin.execute(mock_client, args)

            assert result is True
            mock_client.request.assert_called_once_with(
                "PUT",
                f"/rest/api/2/issue/{issue_key}",
                json_data={
                    "fields": {
                        "customfield_10000": {"value": False},
                        "customfield_10001": "",
                    }
                },
            )

    @patch("jira_creator.plugins.unblock_plugin.EnvFetcher")
    def test_rest_operation_with_different_field_ids(self, mock_env_fetcher):
        """Test REST operation with different custom field IDs."""
        # Test with different field IDs
        mock_env_fetcher.get.side_effect = lambda key: {
            "JIRA_BLOCKED_FIELD": "customfield_20000",
            "JIRA_BLOCKED_REASON_FIELD": "customfield_20001",
        }.get(key)

        plugin = UnblockPlugin()
        mock_client = Mock()

        plugin.rest_operation(mock_client, issue_key="TEST-456")

        mock_client.request.assert_called_once_with(
            "PUT",
            "/rest/api/2/issue/TEST-456",
            json_data={
                "fields": {
                    "customfield_20000": {"value": False},
                    "customfield_20001": "",
                }
            },
        )

    @patch("jira_creator.plugins.unblock_plugin.EnvFetcher")
    def test_rest_operation_with_api_response(self, mock_env_fetcher):
        """Test REST operation returns the API response."""
        mock_env_fetcher.get.side_effect = lambda key: {
            "JIRA_BLOCKED_FIELD": "customfield_10000",
            "JIRA_BLOCKED_REASON_FIELD": "customfield_10001",
        }.get(key)

        plugin = UnblockPlugin()
        mock_client = Mock()
        expected_response = {"key": "TEST-123", "fields": {"status": "unblocked"}}
        mock_client.request.return_value = expected_response

        result = plugin.rest_operation(mock_client, issue_key="TEST-123")

        assert result == expected_response
