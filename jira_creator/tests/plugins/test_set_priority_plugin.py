#!/usr/bin/env python
"""Tests for the set priority plugin."""

from argparse import Namespace
from unittest.mock import Mock

import pytest

from jira_creator.plugins.set_priority_plugin import SetPriorityError, SetPriorityPlugin


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

    def test_get_fix_capabilities(self):
        """Test get_fix_capabilities returns expected capabilities - covers line 93."""
        plugin = SetPriorityPlugin()

        capabilities = plugin.get_fix_capabilities()

        assert isinstance(capabilities, list)
        assert len(capabilities) == 1
        assert capabilities[0]["method_name"] == "set_priority"
        assert "description" in capabilities[0]
        assert "params" in capabilities[0]
        assert "conditions" in capabilities[0]

    def test_execute_fix_success_with_priority(self):
        """Test execute_fix with priority specified - covers lines 117-127."""
        plugin = SetPriorityPlugin()
        mock_client = Mock()
        mock_client.request.return_value = {"key": "TEST-123"}

        args = {"issue_key": "TEST-123", "priority": "major"}
        result = plugin.execute_fix(mock_client, "set_priority", args)

        assert result is True
        mock_client.request.assert_called_once()

    def test_execute_fix_success_default_priority(self):
        """Test execute_fix without priority (uses default 'normal') - covers lines 117-127."""
        plugin = SetPriorityPlugin()
        mock_client = Mock()
        mock_client.request.return_value = {"key": "TEST-123"}

        args = {"issue_key": "TEST-123"}  # No priority specified
        result = plugin.execute_fix(mock_client, "set_priority", args)

        assert result is True
        # Should use default 'normal' priority (normalized to 'Normal')
        call_args = mock_client.request.call_args[1]["json_data"]
        assert call_args["fields"]["priority"]["name"] == "Normal"

    def test_execute_fix_invalid_priority(self):
        """Test execute_fix with invalid priority falls back to 'normal' - covers lines 122-123."""
        plugin = SetPriorityPlugin()
        mock_client = Mock()
        mock_client.request.return_value = {"key": "TEST-123"}

        args = {"issue_key": "TEST-123", "priority": "invalid"}
        result = plugin.execute_fix(mock_client, "set_priority", args)

        assert result is True
        # Should fallback to 'normal' (normalized to 'Normal')
        call_args = mock_client.request.call_args[1]["json_data"]
        assert call_args["fields"]["priority"]["name"] == "Normal"

    def test_execute_fix_unknown_method(self):
        """Test execute_fix with unknown method - covers line 129."""
        plugin = SetPriorityPlugin()
        mock_client = Mock()

        args = {"issue_key": "TEST-123"}
        result = plugin.execute_fix(mock_client, "unknown_method", args)

        assert result is False
