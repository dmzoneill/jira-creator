#!/usr/bin/env python
"""Tests for the update description plugin."""

from argparse import ArgumentParser, Namespace
from unittest.mock import Mock, mock_open, patch

import pytest

from jira_creator.plugins.update_description_plugin import UpdateDescriptionError, UpdateDescriptionPlugin


class TestUpdateDescriptionPlugin:
    """Test cases for UpdateDescriptionPlugin."""

    def test_plugin_properties(self):
        """Test plugin properties are set correctly."""
        plugin = UpdateDescriptionPlugin()
        assert plugin.command_name == "update-description"
        assert plugin.help_text == "Update the description of a Jira issue from file or stdin"

    def test_register_arguments(self):
        """Test argument registration."""
        plugin = UpdateDescriptionPlugin()
        mock_parser = Mock(spec=ArgumentParser)
        mock_group = Mock()
        mock_parser.add_mutually_exclusive_group.return_value = mock_group

        plugin.register_arguments(mock_parser)

        # Check that mutually exclusive group was created
        assert mock_parser.add_mutually_exclusive_group.called
        # issue_key is added to parser, --file and --stdin to the group
        assert mock_parser.add_argument.call_count == 1  # issue_key
        assert mock_group.add_argument.call_count == 2  # --file, --stdin

    def test_rest_operation(self):
        """Test the REST operation directly."""
        plugin = UpdateDescriptionPlugin()
        mock_client = Mock()
        mock_response = {}
        mock_client.request.return_value = mock_response

        plugin.rest_operation(mock_client, issue_key="TEST-123", description="New description")

        mock_client.request.assert_called_once()
        call_args = mock_client.request.call_args
        assert call_args[0][0] == "PUT"
        assert "TEST-123" in call_args[0][1]
        assert call_args[1]["json_data"]["fields"]["description"] == "New description"

    def test_execute_with_file(self):
        """Test successful execution with file input."""
        plugin = UpdateDescriptionPlugin()
        mock_client = Mock()
        mock_client.request.return_value = {}

        args = Namespace(issue_key="TEST-123", file="description.txt", stdin=False)

        mock_file_content = "This is the new description"
        with patch("builtins.open", mock_open(read_data=mock_file_content)):
            with patch("pathlib.Path.exists", return_value=True):
                with patch("builtins.print") as mock_print:
                    result = plugin.execute(mock_client, args)

        assert result is True
        mock_print.assert_called_once()
        assert "✅ Updated description for TEST-123" in mock_print.call_args[0][0]

    def test_execute_with_stdin(self):
        """Test successful execution with stdin input."""
        plugin = UpdateDescriptionPlugin()
        mock_client = Mock()
        mock_client.request.return_value = {}

        args = Namespace(issue_key="TEST-456", file=None, stdin=True)

        mock_stdin_content = "Description from stdin"
        with patch("sys.stdin.read", return_value=mock_stdin_content):
            with patch("builtins.print") as mock_print:
                result = plugin.execute(mock_client, args)

        assert result is True
        assert "✅ Updated description for TEST-456" in mock_print.call_args[0][0]

    def test_execute_with_file_not_found(self):
        """Test execution when file doesn't exist."""
        plugin = UpdateDescriptionPlugin()
        mock_client = Mock()

        args = Namespace(issue_key="TEST-789", file="nonexistent.txt", stdin=False)

        with patch("pathlib.Path.exists", return_value=False):
            with pytest.raises(UpdateDescriptionError, match="File not found"):
                plugin.execute(mock_client, args)

    def test_execute_with_file_read_error(self):
        """Test execution when file read fails."""
        plugin = UpdateDescriptionPlugin()
        mock_client = Mock()

        args = Namespace(issue_key="TEST-789", file="error.txt", stdin=False)

        with patch("pathlib.Path.exists", return_value=True):
            with patch("builtins.open", side_effect=IOError("Permission denied")):
                with pytest.raises(UpdateDescriptionError, match="Failed to read file"):
                    plugin.execute(mock_client, args)

    def test_execute_with_update_error(self):
        """Test execution when update fails."""
        plugin = UpdateDescriptionPlugin()
        mock_client = Mock()
        mock_client.request.side_effect = UpdateDescriptionError("API error")

        args = Namespace(issue_key="TEST-999", file="description.txt", stdin=False)

        with patch("builtins.open", mock_open(read_data="New description")):
            with patch("pathlib.Path.exists", return_value=True):
                with patch("builtins.print") as mock_print:
                    with pytest.raises(UpdateDescriptionError):
                        plugin.execute(mock_client, args)

        # Check error message was printed
        print_calls = [call[0][0] for call in mock_print.call_args_list]
        assert any("❌ Failed to update description" in str(call) for call in print_calls)

    def test_read_from_file(self):
        """Test reading description from file."""
        plugin = UpdateDescriptionPlugin()

        mock_content = "File content here"
        with patch("builtins.open", mock_open(read_data=mock_content)):
            with patch("pathlib.Path.exists", return_value=True):
                result = plugin._read_from_file("test.txt")  # pylint: disable=protected-access

        assert result == mock_content

    def test_read_from_stdin(self):
        """Test reading description from stdin."""
        plugin = UpdateDescriptionPlugin()

        mock_stdin = "Stdin content here"
        with patch("sys.stdin.read", return_value=mock_stdin):
            result = plugin._read_from_stdin()  # pylint: disable=protected-access

        assert result == mock_stdin

    def test_execute_with_no_input_source(self):
        """Test execution when neither file nor stdin is provided."""
        plugin = UpdateDescriptionPlugin()
        mock_client = Mock()

        # Create args where both file and stdin are None/False (edge case)
        args = Namespace(issue_key="TEST-111", file=None, stdin=False)

        with pytest.raises(UpdateDescriptionError, match="No input source specified"):
            plugin.execute(mock_client, args)
