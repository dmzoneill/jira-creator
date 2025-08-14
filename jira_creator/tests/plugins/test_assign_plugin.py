#!/usr/bin/env python
"""Tests for the assign plugin."""

from argparse import Namespace
from unittest.mock import Mock

import pytest

from jira_creator.exceptions.exceptions import AssignIssueError
from jira_creator.plugins.assign_plugin import AssignPlugin


class TestAssignPlugin:
    """Test cases for AssignPlugin."""

    def test_plugin_properties(self):
        """Test plugin properties are set correctly."""
        plugin = AssignPlugin()
        assert plugin.command_name == "assign"
        assert plugin.help_text == "Assign a Jira issue to a user"

    def test_register_arguments(self):
        """Test argument registration."""
        plugin = AssignPlugin()
        mock_parser = Mock()

        plugin.register_arguments(mock_parser)

        assert mock_parser.add_argument.call_count == 2
        calls = mock_parser.add_argument.call_args_list

        # Check issue_key argument
        assert calls[0][0][0] == "issue_key"
        assert calls[0][1]["help"] == "The Jira issue key (e.g., PROJ-123)"

        # Check assignee argument
        assert calls[1][0][0] == "assignee"
        assert calls[1][1]["help"] == "Username of the person to assign the issue to"

    def test_rest_operation(self):
        """Test the REST operation for assigning an issue."""
        plugin = AssignPlugin()
        mock_client = Mock()

        result = plugin.rest_operation(mock_client, issue_key="TEST-123", assignee="john.doe")

        # Verify the correct API call was made
        mock_client.request.assert_called_once_with(
            "PUT",
            "/rest/api/2/issue/TEST-123",
            json_data={"fields": {"assignee": {"name": "john.doe"}}},
        )
        assert result == mock_client.request.return_value

    def test_execute_success(self):
        """Test successful execution of assign command."""
        plugin = AssignPlugin()
        mock_client = Mock()

        args = Namespace(issue_key="TEST-123", assignee="john.doe")

        result = plugin.execute(mock_client, args)

        assert result is True
        mock_client.request.assert_called_once()

    def test_execute_success_prints_message(self, capsys):
        """Test that success message is printed."""
        plugin = AssignPlugin()
        mock_client = Mock()

        args = Namespace(issue_key="TEST-123", assignee="john.doe")

        plugin.execute(mock_client, args)

        captured = capsys.readouterr()
        assert "✅ Issue TEST-123 assigned to john.doe" in captured.out

    def test_execute_failure(self):
        """Test handling of AssignIssueError during execution."""
        plugin = AssignPlugin()
        mock_client = Mock()
        mock_client.request.side_effect = AssignIssueError("User not found")

        args = Namespace(issue_key="TEST-123", assignee="nonexistent.user")

        with pytest.raises(AssignIssueError) as exc_info:
            plugin.execute(mock_client, args)

        assert "User not found" in str(exc_info.value)

    def test_execute_failure_prints_message(self, capsys):
        """Test that error message is printed on failure."""
        plugin = AssignPlugin()
        mock_client = Mock()
        mock_client.request.side_effect = AssignIssueError("Permission denied")

        args = Namespace(issue_key="TEST-123", assignee="john.doe")

        with pytest.raises(AssignIssueError):
            plugin.execute(mock_client, args)

        captured = capsys.readouterr()
        assert "❌ Failed to assign issue: Permission denied" in captured.out

    def test_execute_with_different_issue_keys(self):
        """Test execution with various issue key formats."""
        plugin = AssignPlugin()
        mock_client = Mock()

        # Test with different issue key formats
        test_cases = [
            ("PROJ-123", "user1"),
            ("ABC-1", "user2"),
            ("LONGPROJECT-99999", "user3.name"),
        ]

        for issue_key, assignee in test_cases:
            mock_client.reset_mock()
            args = Namespace(issue_key=issue_key, assignee=assignee)

            result = plugin.execute(mock_client, args)

            assert result is True
            mock_client.request.assert_called_once_with(
                "PUT",
                f"/rest/api/2/issue/{issue_key}",
                json_data={"fields": {"assignee": {"name": assignee}}},
            )
