#!/usr/bin/env python
"""Tests for the add flag plugin."""

from argparse import Namespace
from unittest.mock import Mock

import pytest

from jira_creator.plugins.add_flag_plugin import AddFlagPlugin


class TestAddFlagPlugin:
    """Test cases for AddFlagPlugin."""

    def test_plugin_properties(self):
        """Test plugin properties are set correctly."""
        plugin = AddFlagPlugin()
        assert plugin.command_name == "add-flag"
        assert plugin.help_text == "Add a flag to a Jira issue"

    def test_register_arguments(self):
        """Test argument registration."""
        plugin = AddFlagPlugin()
        mock_parser = Mock()

        plugin.register_arguments(mock_parser)

        mock_parser.add_argument.assert_called_once_with("issue_key", help="The Jira issue key (e.g., PROJ-123)")

    def test_rest_operation(self):
        """Test the REST operation for adding a flag."""
        plugin = AddFlagPlugin()
        mock_client = Mock()

        result = plugin.rest_operation(mock_client, issue_key="TEST-123")

        # Verify the correct API call was made
        mock_client.request.assert_called_once_with(
            "POST",
            "/rest/greenhopper/1.0/xboard/issue/flag/flag.json",
            json_data={"issueKeys": ["TEST-123"], "flag": True},
        )
        assert result == mock_client.request.return_value

    def test_execute_success(self):
        """Test successful execution of add flag command."""
        plugin = AddFlagPlugin()
        mock_client = Mock()

        args = Namespace(issue_key="TEST-123")

        result = plugin.execute(mock_client, args)

        assert result is True
        mock_client.request.assert_called_once()

    def test_execute_failure(self):
        """Test handling of API errors during execution."""
        plugin = AddFlagPlugin()
        mock_client = Mock()
        mock_client.request.side_effect = Exception("API Error")

        args = Namespace(issue_key="TEST-123")

        with pytest.raises(Exception) as exc_info:
            plugin.execute(mock_client, args)

        assert "Failed to add flag: API Error" in str(exc_info.value)

    def test_execute_prints_success_message(self, capsys):
        """Test that success message is printed."""
        plugin = AddFlagPlugin()
        mock_client = Mock()

        args = Namespace(issue_key="TEST-123")

        plugin.execute(mock_client, args)

        captured = capsys.readouterr()
        assert "🚩 Flag added to TEST-123" in captured.out

    def test_execute_prints_error_message(self, capsys):
        """Test that error message is printed on failure."""
        plugin = AddFlagPlugin()
        mock_client = Mock()
        mock_client.request.side_effect = Exception("Network error")

        args = Namespace(issue_key="TEST-123")

        with pytest.raises(Exception):
            plugin.execute(mock_client, args)

        captured = capsys.readouterr()
        assert "❌ Failed to add flag: Network error" in captured.out
