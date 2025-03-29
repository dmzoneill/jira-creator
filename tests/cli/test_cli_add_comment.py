from rh_jira import JiraCLI
from unittest.mock import MagicMock


def test_add_comment_with_text(monkeypatch, capsys):
    cli = JiraCLI()
    cli.jira.add_comment = MagicMock()
    cli.ai_provider.improve_text = MagicMock(return_value="Cleaned")

    class Args:
        issue_key = "AAP-999"
        text = "Raw comment"

    cli.add_comment(Args())
    cli.jira.add_comment.assert_called_once_with("AAP-999", "Cleaned")
    out = capsys.readouterr().out
    assert "✅ Comment added" in out
