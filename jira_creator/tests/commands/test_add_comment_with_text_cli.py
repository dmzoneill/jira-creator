from unittest.mock import MagicMock


def test_add_comment_with_text(cli, capsys):
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
