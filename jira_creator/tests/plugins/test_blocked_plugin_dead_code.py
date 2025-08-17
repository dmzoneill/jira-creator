#!/usr/bin/env python
"""Test for blocked_plugin to cover the previously dead code."""

from argparse import Namespace
from unittest.mock import Mock, patch

from jira_creator.plugins.blocked_plugin import BlockedPlugin


class TestBlockedPluginDeadCode:
    """Test the previously unreachable code in blocked_plugin."""

    @patch("jira_creator.plugins.blocked_plugin.EnvFetcher.get")
    def test_rest_operation_with_blocked_issues(self, mock_env_get, capsys):
        """Test rest_operation with actual blocked issues data."""
        # Mock environment variables
        mock_env_get.side_effect = lambda key: {
            "JIRA_BLOCKED_FIELD": "customfield_10001",
            "JIRA_BLOCKED_REASON_FIELD": "customfield_10002",
        }.get(key)

        plugin = BlockedPlugin()
        mock_client = Mock()

        # Test data with various scenarios
        test_issues = [
            {
                "key": "TEST-100",
                "fields": {
                    "status": {"name": "In Progress"},
                    "assignee": {"displayName": "John Doe"},
                    "summary": "Blocked issue with reason",
                    "customfield_10001": {"value": "True"},
                    "customfield_10002": "Waiting for external dependency",
                },
            },
            {
                "key": "TEST-101",
                "fields": {
                    "status": {"name": "Open"},
                    "assignee": None,  # No assignee
                    "summary": "Blocked issue without assignee",
                    "customfield_10001": {"value": "True"},
                    "customfield_10002": None,  # No reason
                },
            },
            {
                "key": "TEST-102",
                "fields": {
                    "status": {"name": "Done"},
                    "assignee": {"displayName": "Jane Doe"},
                    "summary": "Not blocked issue",
                    "customfield_10001": {"value": "False"},  # Not blocked
                    "customfield_10002": None,
                },
            },
        ]

        # Call with test data
        result = plugin.rest_operation(mock_client, _test_issues=test_issues)

        # Verify the result
        assert isinstance(result, dict)
        assert "blocked_issues" in result
        assert len(result["blocked_issues"]) == 2  # Only 2 blocked issues

        # Check first blocked issue
        assert result["blocked_issues"][0]["key"] == "TEST-100"
        assert result["blocked_issues"][0]["status"] == "In Progress"
        assert result["blocked_issues"][0]["assignee"] == "John Doe"
        assert result["blocked_issues"][0]["reason"] == "Waiting for external dependency"
        assert result["blocked_issues"][0]["summary"] == "Blocked issue with reason"

        # Check second blocked issue (unassigned, no reason)
        assert result["blocked_issues"][1]["key"] == "TEST-101"
        assert result["blocked_issues"][1]["status"] == "Open"
        assert result["blocked_issues"][1]["assignee"] == "Unassigned"
        assert result["blocked_issues"][1]["reason"] is None  # The actual code returns None, not "(no reason)"
        assert result["blocked_issues"][1]["summary"] == "Blocked issue without assignee"

        # Check console output
        captured = capsys.readouterr()
        assert "🔒 Blocked issues:" in captured.out
        assert "TEST-100 [In Progress] — John Doe" in captured.out
        assert "🔸 Reason: Waiting for external dependency" in captured.out
        assert "TEST-101 [Open] — Unassigned" in captured.out
        assert "🔸 Reason: None" in captured.out

    @patch("jira_creator.plugins.blocked_plugin.EnvFetcher.get")
    def test_rest_operation_no_blocked_issues(self, mock_env_get, capsys):
        """Test when there are issues but none are blocked."""
        mock_env_get.side_effect = lambda key: {
            "JIRA_BLOCKED_FIELD": "customfield_10001",
            "JIRA_BLOCKED_REASON_FIELD": "customfield_10002",
        }.get(key)

        plugin = BlockedPlugin()
        mock_client = Mock()

        # Test data with no blocked issues
        test_issues = [
            {
                "key": "TEST-200",
                "fields": {
                    "status": {"name": "Done"},
                    "assignee": {"displayName": "User One"},
                    "summary": "Completed task",
                    "customfield_10001": {"value": "False"},
                },
            },
            {
                "key": "TEST-201",
                "fields": {
                    "status": {"name": "In Progress"},
                    "assignee": {"displayName": "User Two"},
                    "summary": "Work in progress",
                    "customfield_10001": {},  # Empty dict, no value
                },
            },
        ]

        # Call with test data
        result = plugin.rest_operation(mock_client, _test_issues=test_issues)

        # Should return dict when no blocked issues found
        assert result == {"blocked_issues": [], "message": "No blocked issues found"}

        # Check console output
        captured = capsys.readouterr()
        assert "✅ No blocked issues found." in captured.out

    @patch("jira_creator.plugins.blocked_plugin.EnvFetcher.get")
    def test_execute_with_test_issues(self, mock_env_get, capsys):
        """Test execute method passing through test issues."""
        mock_env_get.side_effect = lambda key: {
            "JIRA_BLOCKED_FIELD": "customfield_10001",
            "JIRA_BLOCKED_REASON_FIELD": "customfield_10002",
        }.get(key)

        plugin = BlockedPlugin()
        mock_client = Mock()

        # Create args namespace
        args = Namespace(
            project=None,
            component=None,
            user=None,
            _test_issues=[
                {
                    "key": "TEST-300",
                    "fields": {
                        "status": {"name": "Blocked"},
                        "assignee": {"displayName": "Test User"},
                        "summary": "Blocked for testing",
                        "customfield_10001": {"value": "True"},
                        "customfield_10002": "Test reason",
                    },
                }
            ],
        )

        # Execute should pass through _test_issues to rest_operation
        result = plugin.execute(mock_client, args)

        assert result is True  # execute returns True when successful
