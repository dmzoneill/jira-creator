#!/usr/bin/env python
"""Tests for the remove flag plugin."""

from argparse import Namespace
from unittest.mock import Mock

import pytest

from jira_creator.exceptions.exceptions import RemoveFlagError
from jira_creator.plugins.remove_flag_plugin import RemoveFlagPlugin


class TestRemoveFlagPlugin:
    """Test cases for RemoveFlagPlugin."""

    def test_plugin_properties(self):
        """Test plugin properties are set correctly."""
        plugin = RemoveFlagPlugin()
        assert plugin.command_name == "remove-flag"
        assert plugin.help_text == "Remove a flag from a Jira issue"

    def test_register_arguments(self):
        """Test argument registration."""
        plugin = RemoveFlagPlugin()
        mock_parser = Mock()

        plugin.register_arguments(mock_parser)

        mock_parser.add_argument.assert_called_once_with("issue_key", help="The Jira issue key (e.g., PROJ-123)")

    def test_rest_operation(self):
        """Test the REST operation for removing a flag."""
        plugin = RemoveFlagPlugin()
        mock_client = Mock()

        result = plugin.rest_operation(mock_client, issue_key="TEST-123")

        # Verify the correct API call was made
        mock_client.request.assert_called_once_with(
            "POST",
            "/rest/greenhopper/1.0/xboard/issue/flag/flag.json",
            json_data={"issueKeys": ["TEST-123"], "flag": False},
        )
        assert result == mock_client.request.return_value

    def test_execute_success(self):
        """Test successful execution of remove flag command."""
        plugin = RemoveFlagPlugin()
        mock_client = Mock()

        args = Namespace(issue_key="TEST-123")

        result = plugin.execute(mock_client, args)

        assert result is True
        mock_client.request.assert_called_once()

    def test_execute_failure(self):
        """Test handling of API errors during execution."""
        plugin = RemoveFlagPlugin()
        mock_client = Mock()
        mock_client.request.side_effect = RemoveFlagError("API Error")

        args = Namespace(issue_key="TEST-123")

        with pytest.raises(RemoveFlagError) as exc_info:
            plugin.execute(mock_client, args)

        # The RemoveFlagError is wrapped in another RemoveFlagError
        assert "API Error" in str(exc_info.value)

    def test_execute_prints_success_message(self, capsys):
        """Test that success message is printed."""
        plugin = RemoveFlagPlugin()
        mock_client = Mock()

        args = Namespace(issue_key="TEST-123")

        plugin.execute(mock_client, args)

        captured = capsys.readouterr()
        assert "✅ Removed flag from issue 'TEST-123'" in captured.out

    def test_execute_prints_error_message(self, capsys):
        """Test that error message is printed on failure."""
        plugin = RemoveFlagPlugin()
        mock_client = Mock()
        mock_client.request.side_effect = RemoveFlagError("Network error")

        args = Namespace(issue_key="TEST-123")

        with pytest.raises(RemoveFlagError):
            plugin.execute(mock_client, args)

        captured = capsys.readouterr()
        assert "❌ Failed to remove flag: Network error" in captured.out

    def test_execute_generic_exception_not_caught(self):
        """Test that generic exceptions are not caught by the plugin."""
        plugin = RemoveFlagPlugin()
        mock_client = Mock()
        # Simulate a generic exception from rest_operation
        mock_client.request.side_effect = Exception("Generic error")

        args = Namespace(issue_key="TEST-123")

        # The plugin does not catch generic exceptions, only RemoveFlagError
        with pytest.raises(Exception) as exc_info:
            plugin.execute(mock_client, args)

        assert "Generic error" in str(exc_info.value)
