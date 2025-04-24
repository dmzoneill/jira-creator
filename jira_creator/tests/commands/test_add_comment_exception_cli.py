#!/usr/bin/env python
"""
This file contains a test case for the add_comment method of a CLI application. It mocks the add_comment method to
raise an AddCommentError exception and verifies the expected output when the exception is raised. The test case uses
pytest for testing and unittest.mock for mocking objects.

Functions:
- test_add_comment_exception: Mocks the add_comment method of a Jira CLI object to raise an AddCommentError exception
for testing purposes.

Arguments:
- cli: Jira CLI object to be tested.
- capsys: Pytest fixture for capturing stdout and stderr.

Exceptions:
- AddCommentError: Raised when the add_comment method encounters an error.
"""

from unittest.mock import MagicMock

import pytest
from exceptions.exceptions import AddCommentError


def test_add_comment_exception(cli, capsys):
    """
    Mocks the add_comment method of a Jira CLI object to raise an AddCommentError exception for testing purposes.

    Arguments:
    - cli: Jira CLI object to be tested.
    - capsys: Pytest fixture for capturing stdout and stderr.

    Exceptions:
    - AddCommentError: Raised when the add_comment method encounters an error.
    """

    # Mock the add_comment method to raise an exception
    cli.jira.add_comment = MagicMock(side_effect=AddCommentError("fail"))

    # Mock the improve_text method
    cli.ai_provider.improve_text = MagicMock(return_value="text")

    class Args:
        issue_key = "AAP-test_add_comment_exception"
        text = "test"

    with pytest.raises(AddCommentError):
        # Call the add_comment method and handle the exception
        cli.add_comment(Args())

    # Capture the output
    out = capsys.readouterr().out

    # Check the expected output for the exception case
    assert "❌ Failed to add comment" in out
