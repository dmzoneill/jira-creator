#!/usr/bin/env python
"""Tests for the change type plugin."""

from argparse import Namespace
from unittest.mock import Mock

import pytest

from jira_creator.exceptions.exceptions import ChangeTypeError
from jira_creator.plugins.change_type_plugin import ChangeTypePlugin


class TestChangeTypePlugin:
    """Test cases for ChangeTypePlugin."""

    def test_plugin_properties(self):
        """Test plugin properties are set correctly."""
        plugin = ChangeTypePlugin()
        assert plugin.command_name == "change-type"
        assert plugin.help_text == "Change the type of a Jira issue"

    def test_register_arguments(self):
        """Test argument registration."""
        plugin = ChangeTypePlugin()
        mock_parser = Mock()

        plugin.register_arguments(mock_parser)

        # Verify add_argument was called with correct parameters
        assert mock_parser.add_argument.call_count == 2
        calls = mock_parser.add_argument.call_args_list

        # First argument: issue_key
        assert calls[0][0] == ("issue_key",)
        assert calls[0][1]["help"] == "The Jira issue key (e.g., PROJ-123)"

        # Second argument: new_type with choices
        assert calls[1][0] == ("new_type",)
        assert calls[1][1]["choices"] == ["bug", "story", "epic", "task", "spike"]
        assert calls[1][1]["help"] == "The new issue type"

    def test_rest_operation(self):
        """Test the REST operation directly."""
        plugin = ChangeTypePlugin()
        mock_client = Mock()
        mock_client.request.return_value = {
            "key": "TEST-123",
            "fields": {"issuetype": {"name": "Story"}},
        }

        # Test with lowercase type
        result = plugin.rest_operation(mock_client, issue_key="TEST-123", new_type="story")

        # Verify the request was made correctly with capitalized type
        mock_client.request.assert_called_once_with(
            "PUT",
            "/rest/api/2/issue/TEST-123",
            json_data={"fields": {"issuetype": {"name": "Story"}}},  # Should be capitalized
        )

        # Verify return value
        assert result == {"key": "TEST-123", "fields": {"issuetype": {"name": "Story"}}}

    def test_rest_operation_capitalization(self):
        """Test that issue types are properly capitalized."""
        plugin = ChangeTypePlugin()
        mock_client = Mock()

        test_cases = [
            ("bug", "Bug"),
            ("story", "Story"),
            ("epic", "Epic"),
            ("task", "Task"),
            ("spike", "Spike"),
        ]

        for input_type, expected_type in test_cases:
            mock_client.reset_mock()

            plugin.rest_operation(mock_client, issue_key="TEST-123", new_type=input_type)

            call_args = mock_client.request.call_args[1]["json_data"]
            assert call_args["fields"]["issuetype"]["name"] == expected_type

    def test_execute_success(self, capsys):
        """Test successful execution."""
        plugin = ChangeTypePlugin()
        mock_client = Mock()

        args = Namespace(issue_key="TEST-123", new_type="bug")

        result = plugin.execute(mock_client, args)

        # Verify success
        assert result is True
        mock_client.request.assert_called_once()

        # Verify print output
        captured = capsys.readouterr()
        assert "✅ Issue type changed to 'bug'" in captured.out

    def test_execute_failure(self, capsys):
        """Test execution with API failure."""
        plugin = ChangeTypePlugin()
        mock_client = Mock()
        mock_client.request.side_effect = ChangeTypeError("Permission denied")

        args = Namespace(issue_key="TEST-123", new_type="epic")

        # Verify exception is raised
        with pytest.raises(ChangeTypeError) as exc_info:
            plugin.execute(mock_client, args)

        # Verify the exception message
        assert str(exc_info.value) == "Permission denied"

        # Verify print output
        captured = capsys.readouterr()
        assert "❌ Failed to change issue type: Permission denied" in captured.out

    def test_execute_with_all_issue_types(self, capsys):
        """Test execute with all supported issue types."""
        plugin = ChangeTypePlugin()
        mock_client = Mock()

        issue_types = ["bug", "story", "epic", "task", "spike"]

        for issue_type in issue_types:
            mock_client.reset_mock()
            args = Namespace(issue_key="PROJ-456", new_type=issue_type)

            result = plugin.execute(mock_client, args)

            assert result is True

            # Verify the correct capitalized type was sent
            call_args = mock_client.request.call_args[1]["json_data"]
            assert call_args["fields"]["issuetype"]["name"] == issue_type.capitalize()

            # Verify print output
            captured = capsys.readouterr()
            assert f"✅ Issue type changed to '{issue_type}'" in captured.out

    def test_execute_with_network_error(self, capsys):
        """Test execution with network error."""
        plugin = ChangeTypePlugin()
        mock_client = Mock()
        mock_client.request.side_effect = ChangeTypeError("Network timeout")

        args = Namespace(issue_key="PROJ-789", new_type="story")

        with pytest.raises(ChangeTypeError) as exc_info:
            plugin.execute(mock_client, args)

        # Verify error handling
        assert "Network timeout" in str(exc_info.value)
        captured = capsys.readouterr()
        assert "❌ Failed to change issue type: Network timeout" in captured.out
