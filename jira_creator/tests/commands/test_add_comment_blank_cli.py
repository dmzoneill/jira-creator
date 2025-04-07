from unittest.mock import MagicMock


def test_add_comment_blank(cli, capsys):
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
