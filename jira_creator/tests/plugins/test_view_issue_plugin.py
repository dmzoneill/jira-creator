#!/usr/bin/env python
"""Tests for the view issue plugin."""

from argparse import Namespace
from unittest.mock import Mock, patch

import pytest

from jira_creator.exceptions.exceptions import ViewIssueError
from jira_creator.plugins.view_issue_plugin import ViewIssuePlugin


class TestViewIssuePlugin:
    """Test cases for ViewIssuePlugin."""

    def test_plugin_properties(self):
        """Test plugin properties are set correctly."""
        plugin = ViewIssuePlugin()
        assert plugin.command_name == "view-issue"
        assert plugin.help_text == "View detailed information about a Jira issue"

    def test_register_arguments(self):
        """Test argument registration."""
        plugin = ViewIssuePlugin()
        mock_parser = Mock()

        plugin.register_arguments(mock_parser)

        mock_parser.add_argument.assert_called_once_with("issue_key", help="The Jira issue key (e.g., PROJ-123)")

    def test_rest_operation(self):
        """Test the REST operation."""
        plugin = ViewIssuePlugin()
        mock_client = Mock()
        mock_client.request.return_value = {"fields": {"summary": "Test Issue"}}

        result = plugin.rest_operation(mock_client, issue_key="TEST-123")

        mock_client.request.assert_called_once_with("GET", "/rest/api/2/issue/TEST-123")
        assert result == {"fields": {"summary": "Test Issue"}}

    @patch("jira_creator.plugins.view_issue_plugin.EnvFetcher")
    def test_execute_successful(self, mock_env_fetcher):
        """Test successful execution."""
        # Setup environment variable mocks
        mock_env_fetcher.get.side_effect = lambda key, default: {
            "JIRA_ACCEPTANCE_CRITERIA_FIELD": "customfield_10001",
            "JIRA_BLOCKED_FIELD": "customfield_10002",
            "JIRA_BLOCKED_REASON_FIELD": "customfield_10003",
            "JIRA_STORY_POINTS_FIELD": "customfield_10004",
            "JIRA_SPRINT_FIELD": "customfield_10005",
            "JIRA_WORKSTREAM_FIELD": "customfield_10006",
        }.get(key, default)

        plugin = ViewIssuePlugin()
        mock_client = Mock()
        mock_client.request.return_value = {
            "fields": {
                "summary": "Test Issue Summary",
                "description": "Test Description",
                "status": {"name": "In Progress"},
                "assignee": {"displayName": "John Doe"},
                "reporter": {"displayName": "Jane Smith"},
                "priority": {"name": "High"},
                "issuetype": {"name": "Story"},
                "project": {"key": "TEST"},
                "components": [{"name": "Backend"}, {"name": "Frontend"}],
                "created": "2024-01-01T10:00:00",
                "updated": "2024-01-02T10:00:00",
                "labels": ["important", "feature"],
                "customfield_10001": "Given/When/Then criteria",
                "customfield_10002": "True",
                "customfield_10003": "Waiting for approval",
                "customfield_10004": "5",
                "customfield_10005": ["Sprint 1"],
                "customfield_10006": "Platform",
            }
        }

        args = Namespace(issue_key="TEST-123")

        # Capture print output
        with patch("builtins.print") as mock_print:
            result = plugin.execute(mock_client, args)

        assert result is True
        mock_client.request.assert_called_once()

        # Verify print was called with expected header
        print_calls = mock_print.call_args_list
        assert any("📋 Issue: TEST-123" in str(call) for call in print_calls)
        assert any("Test Issue Summary" in str(call) for call in print_calls)

    def test_execute_with_error(self):
        """Test execution with API error."""
        plugin = ViewIssuePlugin()
        mock_client = Mock()
        mock_client.request.side_effect = ViewIssueError("API failed")

        args = Namespace(issue_key="TEST-123")

        with patch("builtins.print") as mock_print:
            with pytest.raises(ViewIssueError):
                plugin.execute(mock_client, args)

        # Verify error message was printed
        mock_print.assert_called_with("❌ Failed to view issue: API failed")

    def test_format_value_dict(self):
        """Test formatting dictionary values."""
        plugin = ViewIssuePlugin()

        value = {"key": "value"}
        result = plugin._format_value(value)
        assert result == "{'key': 'value'}"

    def test_format_value_list(self):
        """Test formatting list values."""
        plugin = ViewIssuePlugin()

        # Non-empty list
        value = ["item1", "item2", "item3"]
        result = plugin._format_value(value)
        assert result == "item1, item2, item3"

        # Empty list
        value = []
        result = plugin._format_value(value)
        assert result == "None"

    def test_format_value_multiline_string(self):
        """Test formatting multiline strings."""
        plugin = ViewIssuePlugin()

        # Short multiline string
        value = "line1\nline2\nline3"
        result = plugin._format_value(value)
        assert result == "line1 / line2 / line3"

        # Long multiline string (should truncate)
        value = "line1\nline2\nline3\nline4\nline5"
        result = plugin._format_value(value)
        assert result == "line1... (truncated)"

    def test_format_value_none(self):
        """Test formatting None values."""
        plugin = ViewIssuePlugin()

        result = plugin._format_value(None)
        assert result == "None"

        result = plugin._format_value("")
        assert result == "None"

    def test_format_value_other(self):
        """Test formatting other types of values."""
        plugin = ViewIssuePlugin()

        # String
        result = plugin._format_value("simple string")
        assert result == "simple string"

        # Number
        result = plugin._format_value(42)
        assert result == "42"

        # Boolean
        result = plugin._format_value(True)
        assert result == "True"

    @patch("jira_creator.plugins.view_issue_plugin.EnvFetcher")
    def test_get_custom_field_mappings(self, mock_env_fetcher):
        """Test getting custom field mappings."""
        mock_env_fetcher.get.side_effect = lambda key, default: {
            "JIRA_ACCEPTANCE_CRITERIA_FIELD": "customfield_10001",
            "JIRA_BLOCKED_FIELD": "customfield_10002",
            "JIRA_BLOCKED_REASON_FIELD": "customfield_10003",
            "JIRA_STORY_POINTS_FIELD": "customfield_10004",
            "JIRA_SPRINT_FIELD": "customfield_10005",
            "JIRA_WORKSTREAM_FIELD": "customfield_10006",
        }.get(key, default)

        plugin = ViewIssuePlugin()
        mappings = plugin._get_custom_field_mappings()

        assert mappings == {
            "customfield_10001": "acceptance criteria",
            "customfield_10002": "blocked",
            "customfield_10003": "blocked reason",
            "customfield_10004": "story points",
            "customfield_10005": "sprint",
            "customfield_10006": "workstream",
        }

    def test_process_fields_with_custom_fields(self):
        """Test processing fields with custom field mappings."""
        plugin = ViewIssuePlugin()

        custom_fields = {
            "customfield_10001": "acceptance criteria",
            "customfield_10002": "blocked",
        }

        fields = {
            "customfield_10001": "AC text",
            "customfield_10002": "True",
            "summary": "Test Summary",
        }

        result = plugin._process_fields(fields, custom_fields)

        assert result == {
            "acceptance criteria": "AC text",
            "blocked": "True",
            "summary": "Test Summary",
        }

    def test_process_fields_special_handling(self):
        """Test processing fields with special handling."""
        plugin = ViewIssuePlugin()

        fields = {
            "components": [{"name": "Comp1"}, {"name": "Comp2"}],
            "issuetype": {"name": "Story"},
            "assignee": {"displayName": "John Doe"},
            "reporter": {"displayName": "Jane Smith"},
            "creator": {"displayName": "Admin User"},
            "priority": {"name": "High"},
            "status": {"name": "In Progress"},
            "project": {"key": "TEST"},
        }

        result = plugin._process_fields(fields, {})

        assert result["component/s"] == ["Comp1", "Comp2"]
        assert result["issue type"] == "Story"
        assert result["assignee"] == "John Doe"
        assert result["reporter"] == "Jane Smith"
        assert result["creator"] == "Admin User"
        assert result["priority"] == "High"
        assert result["status"] == "In Progress"
        assert result["project"] == "TEST"

    def test_process_fields_with_none_values(self):
        """Test processing fields with None values."""
        plugin = ViewIssuePlugin()

        fields = {
            "components": None,
            "issuetype": None,
            "assignee": None,
            "reporter": None,
            "priority": None,
            "status": None,
            "project": None,
        }

        result = plugin._process_fields(fields, {})

        assert result["component/s"] == []
        assert result["assignee"] == "Unassigned"
        assert result["reporter"] == "Unassigned"
        assert "issue type" not in result  # None values are filtered out
        assert "priority" not in result
        assert "status" not in result
        assert "project" not in result

    @patch("jira_creator.plugins.view_issue_plugin.EnvFetcher")
    def test_display_issue_with_minimal_fields(self, mock_env_fetcher):
        """Test displaying issue with minimal fields."""
        mock_env_fetcher.get.return_value = ""

        plugin = ViewIssuePlugin()

        issue_data = {"fields": {"summary": "Minimal Issue"}}

        with patch("builtins.print") as mock_print:
            plugin._display_issue(issue_data, "TEST-1")

        print_calls = [call[0][0] for call in mock_print.call_args_list]
        assert any("📋 Issue: TEST-1" in call for call in print_calls)
        assert any("Minimal Issue" in call for call in print_calls)

    def test_allowed_keys_constant(self):
        """Test that ALLOWED_KEYS is properly defined."""
        plugin = ViewIssuePlugin()

        expected_keys = [
            "acceptance criteria",
            "blocked",
            "blocked reason",
            "assignee",
            "component/s",
            "created",
            "creator",
            "description",
            "issue type",
            "labels",
            "priority",
            "project",
            "reporter",
            "sprint",
            "status",
            "story points",
            "summary",
            "updated",
            "workstream",
        ]

        assert plugin.ALLOWED_KEYS == expected_keys
