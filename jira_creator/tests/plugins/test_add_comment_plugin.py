#!/usr/bin/env python
"""Tests for the add comment plugin."""

from argparse import Namespace
from unittest.mock import Mock

import pytest

from jira_creator.exceptions.exceptions import AddCommentError, AiError
from jira_creator.plugins.add_comment_plugin import AddCommentPlugin


class TestAddCommentPlugin:
    """Test cases for AddCommentPlugin."""

    def test_plugin_properties(self):
        """Test plugin properties are set correctly."""
        plugin = AddCommentPlugin()
        assert plugin.command_name == "add-comment"
        assert plugin.help_text == "Add a comment to a Jira issue"

    def test_rest_operation(self):
        """Test the REST operation directly without any mocking complexity."""
        plugin = AddCommentPlugin()
        mock_client = Mock()

        # Call REST operation
        plugin.rest_operation(mock_client, issue_key="TEST-123", comment="Test comment")

        # Verify the request was made correctly
        mock_client.request.assert_called_once_with(
            "POST",
            "/rest/api/2/issue/TEST-123/comment",
            json_data={"body": "Test comment"},
        )

    def test_execute_with_text_argument(self):
        """Test execute with text provided as argument."""
        # Create plugin with mocked AI provider
        mock_ai = Mock()
        mock_ai.improve_text.return_value = "Improved comment"
        plugin = AddCommentPlugin(ai_provider=mock_ai)

        # Mock client
        mock_client = Mock()

        # Create args
        args = Namespace(issue_key="TEST-123", text="Original comment", no_ai=False)

        # Execute
        result = plugin.execute(mock_client, args)

        # Verify
        assert result is True
        mock_ai.improve_text.assert_called_once()
        mock_client.request.assert_called_once()

    def test_execute_with_no_ai_flag(self):
        """Test execute with AI disabled."""
        plugin = AddCommentPlugin()
        mock_client = Mock()

        args = Namespace(issue_key="TEST-123", text="Original comment", no_ai=True)

        result = plugin.execute(mock_client, args)

        # Verify AI was not called
        assert result is True
        mock_client.request.assert_called_once_with(
            "POST",
            "/rest/api/2/issue/TEST-123/comment",
            json_data={"body": "Original comment"},
        )

    def test_execute_with_editor(self):
        """Test execute when editor is used for input."""

        # Mock editor function that writes to the temp file
        def mock_editor(cmd_list):
            # Extract filename from command
            filename = cmd_list[1]
            with open(filename, "w") as f:
                f.write("Editor comment")

        plugin = AddCommentPlugin(editor_func=mock_editor)
        mock_client = Mock()

        args = Namespace(issue_key="TEST-123", text=None, no_ai=True)  # No text provided

        result = plugin.execute(mock_client, args)

        assert result is True
        # Verify the editor comment was used
        mock_client.request.assert_called_once()
        call_args = mock_client.request.call_args
        assert call_args[1]["json_data"]["body"] == "Editor comment"

    def test_execute_with_empty_comment(self):
        """Test execute with empty comment."""
        plugin = AddCommentPlugin()
        mock_client = Mock()

        args = Namespace(issue_key="TEST-123", text="   ", no_ai=True)  # Empty/whitespace only

        result = plugin.execute(mock_client, args)

        assert result is False
        mock_client.request.assert_not_called()

    def test_execute_with_ai_error(self):
        """Test execute when AI fails but continues with original."""
        mock_ai = Mock()
        mock_ai.improve_text.side_effect = AiError("AI failed")
        plugin = AddCommentPlugin(ai_provider=mock_ai)

        mock_client = Mock()

        args = Namespace(issue_key="TEST-123", text="Original comment", no_ai=False)

        result = plugin.execute(mock_client, args)

        # Should succeed with original comment
        assert result is True
        mock_client.request.assert_called_once()
        call_args = mock_client.request.call_args
        assert call_args[1]["json_data"]["body"] == "Original comment"

    def test_execute_with_api_error(self):
        """Test execute when API call fails."""
        plugin = AddCommentPlugin()
        mock_client = Mock()
        mock_client.request.side_effect = AddCommentError("API failed")

        args = Namespace(issue_key="TEST-123", text="Test comment", no_ai=True)

        with pytest.raises(AddCommentError):
            plugin.execute(mock_client, args)
