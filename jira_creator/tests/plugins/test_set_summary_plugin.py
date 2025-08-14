#!/usr/bin/env python
"""Tests for the set summary plugin."""

from argparse import Namespace
from unittest.mock import Mock

import pytest

from jira_creator.exceptions.exceptions import SetSummaryError
from jira_creator.plugins.set_summary_plugin import SetSummaryPlugin


class TestSetSummaryPlugin:
    """Test cases for SetSummaryPlugin."""

    def test_plugin_properties(self):
        """Test plugin properties are set correctly."""
        plugin = SetSummaryPlugin()
        assert plugin.command_name == "set-summary"
        assert plugin.help_text == "Set the summary of a Jira issue"
        assert plugin.field_name == "summary"
        assert plugin.argument_name == "summary"
        assert plugin.argument_help == "The new summary text for the issue"

    def test_register_arguments(self):
        """Test argument registration."""
        plugin = SetSummaryPlugin()
        mock_parser = Mock()

        plugin.register_arguments(mock_parser)

        # Verify add_argument was called with correct parameters
        assert mock_parser.add_argument.call_count == 2
        calls = mock_parser.add_argument.call_args_list

        # First argument: issue_key
        assert calls[0][0] == ("issue_key",)
        assert calls[0][1]["help"] == "The Jira issue key (e.g., PROJ-123)"

        # Second argument: summary
        assert calls[1][0] == ("summary",)
        assert calls[1][1]["help"] == "The new summary text for the issue"

    def test_rest_operation(self):
        """Test the REST operation directly."""
        plugin = SetSummaryPlugin()
        mock_client = Mock()
        mock_client.request.return_value = {"key": "TEST-123"}

        result = plugin.rest_operation(mock_client, issue_key="TEST-123", value="New summary text")

        # Verify the request
        mock_client.request.assert_called_once_with(
            "PUT",
            "/rest/api/2/issue/TEST-123",
            json_data={"fields": {"summary": "New summary text"}},
        )
        assert result == {"key": "TEST-123"}

    def test_execute_success(self, capsys):
        """Test successful execution."""
        plugin = SetSummaryPlugin()
        mock_client = Mock()
        mock_client.request.return_value = {"key": "TEST-123"}

        args = Namespace(issue_key="TEST-123", summary="Updated issue summary")

        result = plugin.execute(mock_client, args)

        # Verify success
        assert result is True
        mock_client.request.assert_called_once_with(
            "PUT",
            "/rest/api/2/issue/TEST-123",
            json_data={"fields": {"summary": "Updated issue summary"}},
        )

        # Verify print output
        captured = capsys.readouterr()
        assert "✅ Summary for TEST-123 set to 'Updated issue summary'" in captured.out

    def test_execute_failure(self, capsys):
        """Test execution with API failure."""
        plugin = SetSummaryPlugin()
        mock_client = Mock()
        mock_client.request.side_effect = SetSummaryError("Summary too long")

        args = Namespace(issue_key="TEST-123", summary="A" * 300)

        # Verify exception is raised
        with pytest.raises(SetSummaryError) as exc_info:
            plugin.execute(mock_client, args)

        # Verify the exception message
        assert str(exc_info.value) == "Summary too long"

        # Verify print output
        captured = capsys.readouterr()
        assert "❌ Failed to set summary: Summary too long" in captured.out

    def test_execute_with_different_summaries(self):
        """Test execute with different summary texts."""
        plugin = SetSummaryPlugin()
        mock_client = Mock()

        test_summaries = [
            "Fix bug in authentication",
            "Add new feature for data export",
            "Update documentation for API endpoints",
            "Refactor database connection logic",
            "Security patch for XSS vulnerability",
        ]

        for summary in test_summaries:
            mock_client.reset_mock()
            args = Namespace(issue_key="TEST-123", summary=summary)

            result = plugin.execute(mock_client, args)

            assert result is True
            # Verify the summary was passed correctly
            call_args = mock_client.request.call_args[1]["json_data"]
            assert call_args["fields"]["summary"] == summary

    def test_rest_operation_with_special_characters(self):
        """Test REST operation with summaries containing special characters."""
        plugin = SetSummaryPlugin()
        mock_client = Mock()

        special_summaries = [
            "Fix issue with & character handling",
            'Update "quoted" text processing',
            "Handle < and > in XML parsing",
            "Support UTF-8: émojis 🚀 and accents",
            "Fix path\\ with backslash",
            "Support multi-line\nsummaries",
        ]

        for summary in special_summaries:
            mock_client.reset_mock()

            plugin.rest_operation(mock_client, issue_key="TEST-456", value=summary)

            # Verify special characters are preserved
            call_args = mock_client.request.call_args[1]["json_data"]
            assert call_args["fields"]["summary"] == summary

    def test_execute_with_empty_summary(self, capsys):
        """Test execution with empty summary."""
        plugin = SetSummaryPlugin()
        mock_client = Mock()
        mock_client.request.side_effect = SetSummaryError("Summary cannot be empty")

        args = Namespace(issue_key="TEST-123", summary="")

        with pytest.raises(SetSummaryError) as exc_info:
            plugin.execute(mock_client, args)

        assert "Summary cannot be empty" in str(exc_info.value)

        # Verify print output
        captured = capsys.readouterr()
        assert "❌ Failed to set summary:" in captured.out
        assert "Summary cannot be empty" in captured.out

    def test_execute_with_long_summary(self):
        """Test execute with a long summary (within Jira limits)."""
        plugin = SetSummaryPlugin()
        mock_client = Mock()
        mock_client.request.return_value = {"key": "TEST-123"}

        # Jira typically allows summaries up to 255 characters
        # Create a summary that is exactly 255 characters
        base_text = "This is a very long summary that contains many words "
        long_summary = base_text * 5  # This creates a string longer than 255 chars
        truncated_summary = long_summary[:255]

        args = Namespace(issue_key="TEST-123", summary=truncated_summary)

        result = plugin.execute(mock_client, args)

        assert result is True
        # Verify the full summary was passed
        call_args = mock_client.request.call_args[1]["json_data"]
        assert call_args["fields"]["summary"] == truncated_summary
        assert len(call_args["fields"]["summary"]) == 255
