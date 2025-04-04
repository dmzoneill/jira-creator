from unittest.mock import MagicMock

from jira_creator.rh_jira import JiraCLI


def test_add_comment_exception(capsys):
    cli = JiraCLI()

    # Mock the add_comment method to raise an exception
    cli.jira.add_comment = MagicMock(side_effect=Exception("fail"))

    # Mock the improve_text method
    cli.ai_provider.improve_text = MagicMock(return_value="text")

    class Args:
        issue_key = "AAP-7"
        text = "test"

    # Call the add_comment method and handle the exception
    cli.add_comment(Args())

    # Capture the output
    out = capsys.readouterr().out

    # Check the expected output for the exception case
    assert "❌ Failed to add comment" in out
