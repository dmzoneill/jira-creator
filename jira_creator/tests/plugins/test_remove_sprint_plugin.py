#!/usr/bin/env python
"""Tests for the remove sprint plugin."""

from argparse import Namespace
from unittest.mock import Mock

import pytest

from jira_creator.exceptions.exceptions import RemoveFromSprintError
from jira_creator.plugins.remove_sprint_plugin import RemoveSprintPlugin


class TestRemoveSprintPlugin:
    """Test cases for RemoveSprintPlugin."""

    def test_plugin_properties(self):
        """Test plugin properties are set correctly."""
        plugin = RemoveSprintPlugin()
        assert plugin.command_name == "remove-sprint"
        assert plugin.help_text == "Remove an issue from its current sprint"

    def test_register_arguments(self):
        """Test argument registration."""
        plugin = RemoveSprintPlugin()
        mock_parser = Mock()

        plugin.register_arguments(mock_parser)

        mock_parser.add_argument.assert_called_once_with("issue_key", help="The Jira issue key (e.g., PROJ-123)")

    def test_rest_operation(self):
        """Test the REST operation for removing from sprint."""
        plugin = RemoveSprintPlugin()
        mock_client = Mock()

        result = plugin.rest_operation(mock_client, issue_key="TEST-123")

        # Verify the correct API call was made
        mock_client.request.assert_called_once_with(
            "POST", "/rest/agile/1.0/backlog/issue", json_data={"issues": ["TEST-123"]}
        )
        assert result == mock_client.request.return_value

    def test_rest_operation_prints_success(self, capsys):
        """Test that rest_operation prints success message."""
        plugin = RemoveSprintPlugin()
        mock_client = Mock()

        plugin.rest_operation(mock_client, issue_key="TEST-123")

        captured = capsys.readouterr()
        assert "✅ Moved TEST-123 to backlog" in captured.out

    def test_execute_success(self):
        """Test successful execution of remove sprint command."""
        plugin = RemoveSprintPlugin()
        mock_client = Mock()

        args = Namespace(issue_key="TEST-123")

        result = plugin.execute(mock_client, args)

        assert result is True
        mock_client.request.assert_called_once()

    def test_execute_failure(self):
        """Test handling of API errors during execution."""
        plugin = RemoveSprintPlugin()
        mock_client = Mock()
        mock_client.request.side_effect = RemoveFromSprintError("API Error")

        args = Namespace(issue_key="TEST-123")

        with pytest.raises(RemoveFromSprintError) as exc_info:
            plugin.execute(mock_client, args)

        # The RemoveFromSprintError is wrapped in another RemoveFromSprintError
        assert "API Error" in str(exc_info.value)

    def test_execute_prints_success_message(self, capsys):
        """Test that success message is printed."""
        plugin = RemoveSprintPlugin()
        mock_client = Mock()

        args = Namespace(issue_key="TEST-123")

        plugin.execute(mock_client, args)

        captured = capsys.readouterr()
        # Should have both messages: one from rest_operation and one from execute
        assert "✅ Moved TEST-123 to backlog" in captured.out
        assert "✅ Removed from sprint" in captured.out

    def test_execute_prints_error_message(self, capsys):
        """Test that error message is printed on failure."""
        plugin = RemoveSprintPlugin()
        mock_client = Mock()
        mock_client.request.side_effect = RemoveFromSprintError("Network error")

        args = Namespace(issue_key="TEST-123")

        with pytest.raises(RemoveFromSprintError):
            plugin.execute(mock_client, args)

        captured = capsys.readouterr()
        assert "❌ Failed to remove from sprint: Network error" in captured.out

    def test_execute_generic_exception_not_caught(self):
        """Test that generic exceptions are not caught by the plugin."""
        plugin = RemoveSprintPlugin()
        mock_client = Mock()
        # Simulate a generic exception from rest_operation
        mock_client.request.side_effect = Exception("Generic error")

        args = Namespace(issue_key="TEST-123")

        # The plugin does not catch generic exceptions, only RemoveFromSprintError
        with pytest.raises(Exception) as exc_info:
            plugin.execute(mock_client, args)

        assert "Generic error" in str(exc_info.value)
