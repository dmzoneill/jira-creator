#!/usr/bin/env python
"""
This script contains a unit test function test_add_comment_with_text that tests the add_comment method of a CLI class.
It mocks dependencies using MagicMock from unittest.mock. The test verifies that the add_comment method correctly
cleans and adds a comment to a Jira issue, and outputs a success message.

test_add_comment_with_text(cli, capsys) function:
Adds a comment with text using the provided CLI object.

Arguments:
- cli (object): The CLI object containing the necessary methods and attributes.
- capsys (object): The capsys object for capturing stdout and stderr outputs.
"""

from unittest.mock import MagicMock, patch


def test_add_comment_with_text(cli, capsys):
    """
    Adds a comment with text using the provided CLI object.

    Arguments:
    - cli (object): The CLI object containing the necessary methods and attributes.
    - capsys (object): The capsys object for capturing stdout and stderr outputs.
    """

    # Mock the get_ai_provider to return a mock AI provider object
    with patch("commands.cli_add_comment.get_ai_provider") as mock_get_ai_provider:
        # Create a mock AI provider
        mock_ai_provider = MagicMock()
        mock_ai_provider.improve_text.return_value = "Cleaned"
        mock_get_ai_provider.return_value = mock_ai_provider

        # Mock dependencies using MagicMock
        cli.jira = MagicMock()
        cli.jira.add_comment = MagicMock()

        class Args:
            issue_key = "AAP-test_add_comment_with_text"
            text = "Raw comment"

        cli.add_comment(Args())

        cli.jira.add_comment.assert_called_once_with(
            "AAP-test_add_comment_with_text", "Cleaned"
        )
        out = capsys.readouterr().out
        assert "✅ Comment added" in out
