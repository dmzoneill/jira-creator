from jira_creator.rh_jira import JiraCLI


def test_add_comment_blank(monkeypatch, capsys):
    cli = JiraCLI()

    class Args:
        issue_key = "AAP-123"
        text = "   "

    cli.add_comment(Args())
    out = capsys.readouterr().out
    assert "⚠️ No comment provided" in out
