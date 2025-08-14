#!/usr/bin/env python
"""Tests for the unassign plugin."""

from argparse import Namespace
from unittest.mock import Mock

import pytest

from jira_creator.exceptions.exceptions import UnassignIssueError
from jira_creator.plugins.unassign_plugin import UnassignPlugin


class TestUnassignPlugin:
    """Test cases for UnassignPlugin."""

    def test_plugin_properties(self):
        """Test plugin properties are set correctly."""
        plugin = UnassignPlugin()
        assert plugin.command_name == "unassign"
        assert plugin.help_text == "Remove the assignee from a Jira issue"

    def test_register_arguments(self):
        """Test argument registration."""
        plugin = UnassignPlugin()
        mock_parser = Mock()

        plugin.register_arguments(mock_parser)

        mock_parser.add_argument.assert_called_once_with("issue_key", help="The Jira issue key (e.g., PROJ-123)")

    def test_rest_operation(self):
        """Test the REST operation for unassigning an issue."""
        plugin = UnassignPlugin()
        mock_client = Mock()

        result = plugin.rest_operation(mock_client, issue_key="TEST-123")

        # Verify the correct API call was made
        mock_client.request.assert_called_once_with(
            "PUT",
            "/rest/api/2/issue/TEST-123",
            json_data={"fields": {"assignee": None}},
        )
        assert result == mock_client.request.return_value

    def test_execute_success(self):
        """Test successful execution of unassign command."""
        plugin = UnassignPlugin()
        mock_client = Mock()

        args = Namespace(issue_key="TEST-123")

        result = plugin.execute(mock_client, args)

        assert result is True
        mock_client.request.assert_called_once()

    def test_execute_success_prints_message(self, capsys):
        """Test that success message is printed."""
        plugin = UnassignPlugin()
        mock_client = Mock()

        args = Namespace(issue_key="TEST-123")

        plugin.execute(mock_client, args)

        captured = capsys.readouterr()
        assert "✅ Issue TEST-123 unassigned" in captured.out

    def test_execute_failure(self):
        """Test handling of UnassignIssueError during execution."""
        plugin = UnassignPlugin()
        mock_client = Mock()
        mock_client.request.side_effect = UnassignIssueError("Issue not found")

        args = Namespace(issue_key="TEST-123")

        with pytest.raises(UnassignIssueError) as exc_info:
            plugin.execute(mock_client, args)

        assert "Issue not found" in str(exc_info.value)

    def test_execute_failure_prints_message(self, capsys):
        """Test that error message is printed on failure."""
        plugin = UnassignPlugin()
        mock_client = Mock()
        mock_client.request.side_effect = UnassignIssueError("Permission denied")

        args = Namespace(issue_key="TEST-123")

        with pytest.raises(UnassignIssueError):
            plugin.execute(mock_client, args)

        captured = capsys.readouterr()
        assert "❌ Failed to unassign issue: Permission denied" in captured.out

    def test_execute_with_different_issue_keys(self):
        """Test execution with various issue key formats."""
        plugin = UnassignPlugin()
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
                json_data={"fields": {"assignee": None}},
            )

    def test_rest_operation_with_api_response(self):
        """Test REST operation returns the API response."""
        plugin = UnassignPlugin()
        mock_client = Mock()
        expected_response = {"key": "TEST-123", "fields": {"assignee": None}}
        mock_client.request.return_value = expected_response

        result = plugin.rest_operation(mock_client, issue_key="TEST-123")

        assert result == expected_response
