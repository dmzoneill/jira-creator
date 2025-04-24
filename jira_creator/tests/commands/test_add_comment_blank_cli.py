#!/usr/bin/env python
"""
This script contains a unit test function test_add_comment_blank that tests the add_comment method of a CLI
application. It mocks the add_comment method using MagicMock and then calls the method with a blank comment. The test
asserts that the output contains a warning message indicating that no comment was provided.
"""

from unittest.mock import MagicMock


def test_add_comment_blank(cli, capsys):
    """
    Simulate a test for adding a comment in a blank scenario.

    Arguments:
    - cli: The CLI object used to interact with Jira.
    - capsys: A fixture to capture stdout and stderr outputs during testing.

    Side Effects:
    - Mocks the add_comment method of the Jira object in the CLI using MagicMock.
    """

    # Mock add_comment method
    cli.jira.add_comment = MagicMock()

    class Args:
        issue_key = "AAP-test_add_comment_blank"
        text = "   "  # Blank comment

    # Call the method
    cli.add_comment(Args())

    # Capture output and assert
    out = capsys.readouterr().out
    assert "⚠️ No comment provided" in out
