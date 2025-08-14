#!/usr/bin/env python
"""Tests for the set priority plugin."""

from argparse import Namespace
from unittest.mock import Mock

import pytest

from jira_creator.exceptions.exceptions import SetPriorityError
from jira_creator.plugins.set_priority_plugin import SetPriorityPlugin


class TestSetPriorityPlugin:
    """Test cases for SetPriorityPlugin."""

    def test_plugin_properties(self):
        """Test plugin properties are set correctly."""
        plugin = SetPriorityPlugin()
        assert plugin.command_name == "set-priority"
        assert plugin.help_text == "Set the priority of a Jira issue"

    def test_rest_operation(self):
        """Test the REST operation directly - no complex mocking needed!"""
        plugin = SetPriorityPlugin()
        mock_client = Mock()

        # Test with lowercase priority
        plugin.rest_operation(mock_client, issue_key="TEST-123", priority="critical")

        # Verify the request
        mock_client.request.assert_called_once_with(
            "PUT",
            "/rest/api/2/issue/TEST-123",
            json_data={"fields": {"priority": {"name": "Critical"}}},  # Should be capitalized
        )

    def test_priority_normalization(self):
        """Test that priorities are normalized correctly."""
        plugin = SetPriorityPlugin()
        mock_client = Mock()

        test_cases = [
            ("critical", "Critical"),
            ("CRITICAL", "Critical"),
            ("major", "Major"),
            ("normal", "Normal"),
            ("minor", "Minor"),
            ("invalid", "Normal"),  # Default
        ]

        for input_priority, expected_name in test_cases:
            mock_client.reset_mock()

            plugin.rest_operation(mock_client, issue_key="TEST-123", priority=input_priority)

            call_args = mock_client.request.call_args[1]["json_data"]
            assert call_args["fields"]["priority"]["name"] == expected_name

    def test_execute_success(self):
        """Test successful execution."""
        plugin = SetPriorityPlugin()
        mock_client = Mock()

        args = Namespace(issue_key="TEST-123", priority="major")

        result = plugin.execute(mock_client, args)

        assert result is True
        mock_client.request.assert_called_once()

    def test_execute_failure(self):
        """Test execution with API failure."""
        plugin = SetPriorityPlugin()
        mock_client = Mock()
        mock_client.request.side_effect = SetPriorityError("API error")

        args = Namespace(issue_key="TEST-123", priority="major")

        with pytest.raises(SetPriorityError):
            plugin.execute(mock_client, args)
