from unittest.mock import MagicMock

from jira_creator.rh_jira import JiraCLI


def test_add_comment_blank(capsys):
    cli = JiraCLI()

    # Mock add_comment method
    cli.jira.add_comment = MagicMock()

    class Args:
        issue_key = "AAP-123"
        text = "   "  # Blank comment

    # Call the method
    cli.add_comment(Args())

    # Capture output and assert
    out = capsys.readouterr().out
    assert "⚠️ No comment provided" in out
