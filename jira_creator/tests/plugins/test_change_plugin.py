#!/usr/bin/env python
"""Tests for the change plugin."""

from argparse import Namespace
from unittest.mock import Mock

import pytest

from jira_creator.exceptions.exceptions import ChangeTypeError
from jira_creator.plugins.change_plugin import ChangePlugin


class TestChangePlugin:
    """Test cases for ChangePlugin."""

    def test_plugin_properties(self):
        """Test plugin properties are set correctly."""
        plugin = ChangePlugin()
        assert plugin.command_name == "change"
        assert plugin.help_text == "Change issue type"

    def test_register_arguments(self):
        """Test argument registration."""
        plugin = ChangePlugin()
        mock_parser = Mock()

        plugin.register_arguments(mock_parser)

        # Verify add_argument was called with correct parameters
        assert mock_parser.add_argument.call_count == 2
        calls = mock_parser.add_argument.call_args_list

        # First argument: issue_key
        assert calls[0][0] == ("issue_key",)
        assert calls[0][1]["help"] == "The Jira issue id/key"

        # Second argument: new_type
        assert calls[1][0] == ("new_type",)
        assert calls[1][1]["help"] == "New issue type"

    def test_rest_operation(self):
        """Test the REST operation directly."""
        plugin = ChangePlugin()
        mock_client = Mock()

        # Call REST operation
        result = plugin.rest_operation(mock_client, issue_key="TEST-123", new_type="story")

        # Verify the request was made correctly
        mock_client.request.assert_called_once_with(
            "PUT",
            "/rest/api/2/issue/TEST-123",
            json_data={"fields": {"issuetype": {"name": "story"}}},
        )

        # Verify return value
        assert result == {"success": True}

    def test_execute_success(self, capsys):
        """Test successful execution."""
        plugin = ChangePlugin()
        mock_client = Mock()

        args = Namespace(issue_key="TEST-123", new_type="bug")

        result = plugin.execute(mock_client, args)

        # Verify success
        assert result is True
        mock_client.request.assert_called_once()

        # Verify print output
        captured = capsys.readouterr()
        assert "✅ Changed type of TEST-123 to bug" in captured.out

    def test_execute_failure(self, capsys):
        """Test execution with API failure."""
        plugin = ChangePlugin()
        mock_client = Mock()
        mock_client.request.side_effect = ChangeTypeError("API error")

        args = Namespace(issue_key="TEST-123", new_type="epic")

        # Verify exception is raised
        with pytest.raises(ChangeTypeError) as exc_info:
            plugin.execute(mock_client, args)

        # Verify the exception message
        assert str(exc_info.value) == "API error"

        # Verify print output
        captured = capsys.readouterr()
        assert "❌ Failed to change issue type: API error" in captured.out

    def test_execute_with_different_issue_types(self):
        """Test execute with different issue types."""
        plugin = ChangePlugin()
        mock_client = Mock()

        issue_types = ["story", "bug", "epic", "task", "spike"]

        for issue_type in issue_types:
            mock_client.reset_mock()
            args = Namespace(issue_key="TEST-456", new_type=issue_type)

            result = plugin.execute(mock_client, args)

            assert result is True
            # Verify the correct type was sent
            call_args = mock_client.request.call_args[1]["json_data"]
            assert call_args["fields"]["issuetype"]["name"] == issue_type
