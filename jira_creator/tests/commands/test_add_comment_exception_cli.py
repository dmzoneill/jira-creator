from unittest.mock import MagicMock

import pytest
from exceptions.exceptions import AddCommentError


def test_add_comment_exception(cli, capsys):
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
