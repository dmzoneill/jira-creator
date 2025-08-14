#!/usr/bin/env python
"""Tests for the clone issue plugin."""

from argparse import Namespace
from unittest.mock import Mock

import pytest

from jira_creator.exceptions.exceptions import CloneIssueError
from jira_creator.plugins.clone_issue_plugin import CloneIssuePlugin


class TestCloneIssuePlugin:
    """Test cases for CloneIssuePlugin."""

    def test_plugin_properties(self):
        """Test plugin properties are set correctly."""
        plugin = CloneIssuePlugin()
        assert plugin.command_name == "clone-issue"
        assert plugin.help_text == "Create a copy of an existing Jira issue"

    def test_register_arguments(self):
        """Test argument registration."""
        plugin = CloneIssuePlugin()
        mock_parser = Mock()

        plugin.register_arguments(mock_parser)

        # Verify arguments were added
        assert mock_parser.add_argument.call_count == 2
        calls = mock_parser.add_argument.call_args_list

        # Check issue_key argument
        assert calls[0][0][0] == "issue_key"
        assert calls[0][1]["help"] == "The Jira issue key to clone (e.g., PROJ-123)"

        # Check summary-suffix argument
        assert calls[1][0][0] == "-s"
        assert calls[1][0][1] == "--summary-suffix"
        assert calls[1][1]["default"] == " (Clone)"
        assert calls[1][1]["help"] == "Suffix to add to the cloned issue summary (default: ' (Clone)')"

    def test_get_issue_details(self):
        """Test _get_issue_details method."""
        plugin = CloneIssuePlugin()
        mock_client = Mock()
        mock_client.request.return_value = {
            "key": "TEST-123",
            "fields": {
                "summary": "Original Issue",
                "description": "Original Description",
            },
        }

        result = plugin._get_issue_details(mock_client, "TEST-123")

        assert result["key"] == "TEST-123"
        assert result["fields"]["summary"] == "Original Issue"
        mock_client.request.assert_called_once_with("GET", "/rest/api/2/issue/TEST-123")

    def test_rest_operation_basic_fields(self):
        """Test REST operation with basic fields only."""
        plugin = CloneIssuePlugin()
        mock_client = Mock()
        mock_client.request.return_value = {"key": "TEST-456"}

        original_issue = {
            "fields": {
                "project": {"key": "TEST"},
                "summary": "Original Summary",
                "description": "Original Description",
                "issuetype": {"name": "Story"},
                "priority": {"name": "High"},
            }
        }

        result = plugin.rest_operation(mock_client, original_issue=original_issue, summary_suffix=" (Clone)")

        assert result["key"] == "TEST-456"

        # Verify API call
        mock_client.request.assert_called_once_with(
            "POST",
            "/rest/api/2/issue/",
            json_data={
                "fields": {
                    "project": {"key": "TEST"},
                    "summary": "Original Summary (Clone)",
                    "description": "Original Description",
                    "issuetype": {"name": "Story"},
                    "priority": {"name": "High"},
                }
            },
        )

    def test_rest_operation_with_additional_fields(self):
        """Test REST operation with components, labels, and versions."""
        plugin = CloneIssuePlugin()
        mock_client = Mock()
        mock_client.request.return_value = {"key": "TEST-789"}

        original_issue = {
            "fields": {
                "project": {"key": "PROJ"},
                "summary": "Feature Request",
                "description": "Add new feature",
                "issuetype": {"name": "Task"},
                "priority": {"name": "Medium"},
                "components": [{"name": "Backend"}, {"name": "API"}],
                "labels": ["feature", "backend"],
                "versions": [{"name": "1.0"}, {"name": "2.0"}],
            }
        }

        result = plugin.rest_operation(mock_client, original_issue=original_issue, summary_suffix=" - Copy")

        assert result["key"] == "TEST-789"

        # Verify all fields were copied
        call_args = mock_client.request.call_args[1]["json_data"]["fields"]
        assert call_args["summary"] == "Feature Request - Copy"
        assert call_args["components"] == [{"name": "Backend"}, {"name": "API"}]
        assert call_args["labels"] == ["feature", "backend"]
        assert call_args["versions"] == [{"name": "1.0"}, {"name": "2.0"}]

    def test_rest_operation_missing_fields(self):
        """Test REST operation when some fields are missing."""
        plugin = CloneIssuePlugin()
        mock_client = Mock()
        mock_client.request.return_value = {"key": "TEST-999"}

        original_issue = {
            "fields": {
                "project": {"key": "TEST"},
                "summary": "Minimal Issue",
                # Missing description, priority defaults to Normal
                "issuetype": {"name": "Bug"},
            }
        }

        plugin.rest_operation(mock_client, original_issue=original_issue, summary_suffix=" (Cloned)")

        # Verify default values
        call_args = mock_client.request.call_args[1]["json_data"]["fields"]
        assert call_args["summary"] == "Minimal Issue (Cloned)"
        assert call_args["description"] == ""
        assert call_args["priority"]["name"] == "Normal"

    def test_rest_operation_empty_original(self):
        """Test REST operation with empty original issue fields."""
        plugin = CloneIssuePlugin()
        mock_client = Mock()
        mock_client.request.return_value = {"key": "TEST-111"}

        original_issue = {"fields": {}}

        plugin.rest_operation(mock_client, original_issue=original_issue, summary_suffix=" (Clone)")

        # Verify empty/default values were used
        call_args = mock_client.request.call_args[1]["json_data"]["fields"]
        assert call_args["project"]["key"] is None
        assert call_args["summary"] == " (Clone)"
        assert call_args["description"] == ""
        assert call_args["issuetype"]["name"] is None
        assert call_args["priority"]["name"] == "Normal"

    def test_execute_success(self):
        """Test successful execution of clone-issue command."""
        plugin = CloneIssuePlugin()
        mock_client = Mock()

        # Mock _get_issue_details
        plugin._get_issue_details = Mock(
            return_value={
                "fields": {
                    "project": {"key": "TEST"},
                    "summary": "Original",
                    "description": "Desc",
                    "issuetype": {"name": "Story"},
                    "priority": {"name": "High"},
                }
            }
        )

        # Mock rest_operation
        plugin.rest_operation = Mock(return_value={"key": "TEST-456"})

        args = Namespace(issue_key="TEST-123", summary_suffix=" (Clone)")

        result = plugin.execute(mock_client, args)

        assert result is True
        plugin._get_issue_details.assert_called_once_with(mock_client, "TEST-123")
        plugin.rest_operation.assert_called_once()

    def test_execute_prints_success(self, capsys):
        """Test that success message is printed correctly."""
        plugin = CloneIssuePlugin()
        mock_client = Mock()

        plugin._get_issue_details = Mock(return_value={"fields": {}})
        plugin.rest_operation = Mock(return_value={"key": "TEST-456"})

        args = Namespace(issue_key="TEST-123", summary_suffix=" (Clone)")

        plugin.execute(mock_client, args)

        captured = capsys.readouterr()
        assert "✅ Issue cloned: TEST-123 → TEST-456" in captured.out

    def test_execute_get_issue_fails(self):
        """Test execution when getting original issue fails."""
        plugin = CloneIssuePlugin()
        mock_client = Mock()

        plugin._get_issue_details = Mock(side_effect=CloneIssueError("Issue not found"))

        args = Namespace(issue_key="TEST-123", summary_suffix=" (Clone)")

        with pytest.raises(CloneIssueError):
            plugin.execute(mock_client, args)

    def test_execute_rest_operation_fails(self):
        """Test execution when REST operation fails."""
        plugin = CloneIssuePlugin()
        mock_client = Mock()

        plugin._get_issue_details = Mock(return_value={"fields": {}})
        plugin.rest_operation = Mock(side_effect=CloneIssueError("API error"))

        args = Namespace(issue_key="TEST-123", summary_suffix=" (Clone)")

        with pytest.raises(CloneIssueError):
            plugin.execute(mock_client, args)

    def test_execute_prints_error(self, capsys):
        """Test that error message is printed correctly."""
        plugin = CloneIssuePlugin()
        mock_client = Mock()

        plugin._get_issue_details = Mock(side_effect=CloneIssueError("Network error"))

        args = Namespace(issue_key="TEST-123", summary_suffix=" (Clone)")

        with pytest.raises(CloneIssueError):
            plugin.execute(mock_client, args)

        captured = capsys.readouterr()
        assert "❌ Failed to clone issue: Network error" in captured.out

    def test_execute_missing_key_in_response(self):
        """Test execution when response doesn't contain key."""
        plugin = CloneIssuePlugin()
        mock_client = Mock()

        plugin._get_issue_details = Mock(return_value={"fields": {}})
        # Return response without 'key'
        plugin.rest_operation = Mock(return_value={})

        args = Namespace(issue_key="TEST-123", summary_suffix=" (Clone)")

        result = plugin.execute(mock_client, args)

        # Should still succeed but key will be None in print
        assert result is True

    def test_execute_with_custom_suffix(self, capsys):
        """Test execution with custom summary suffix."""
        plugin = CloneIssuePlugin()
        mock_client = Mock()

        plugin._get_issue_details = Mock(return_value={"fields": {"summary": "Original Issue"}})
        plugin.rest_operation = Mock(return_value={"key": "TEST-789"})

        args = Namespace(issue_key="TEST-123", summary_suffix=" - BACKUP")

        plugin.execute(mock_client, args)

        # Verify custom suffix was passed
        rest_call_args = plugin.rest_operation.call_args[1]
        assert rest_call_args["summary_suffix"] == " - BACKUP"

        captured = capsys.readouterr()
        assert "✅ Issue cloned: TEST-123 → TEST-789" in captured.out
