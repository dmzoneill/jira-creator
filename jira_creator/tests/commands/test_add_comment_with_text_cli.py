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

from unittest.mock import MagicMock


def test_add_comment_with_text(cli, capsys):
    """
    Adds a comment with text using the provided CLI object.

    Arguments:
    - cli (object): The CLI object containing the necessary methods and attributes.
    - capsys (object): The capsys object for capturing stdout and stderr outputs.
    """

    # Mock dependencies using MagicMock
    cli.jira = MagicMock()
    cli.jira.add_comment = MagicMock()

    cli.ai_provider = MagicMock()
    cli.ai_provider.improve_text = MagicMock(return_value="Cleaned")

    class Args:
        issue_key = "AAP-test_add_comment_with_text"
        text = "Raw comment"

    cli.add_comment(Args())

    cli.jira.add_comment.assert_called_once_with(
        "AAP-test_add_comment_with_text", "Cleaned"
    )
    out = capsys.readouterr().out
    assert "✅ Comment added" in out
