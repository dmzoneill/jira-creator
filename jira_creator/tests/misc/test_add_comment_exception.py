from jira_creator.rh_jira import JiraCLI


def test_add_comment_exception(monkeypatch, capsys):
    cli = JiraCLI()
    cli.jira.add_comment = lambda *a, **k: (_ for _ in ()).throw(Exception("fail"))
    cli.ai_provider.improve_text = lambda *a, **k: "text"

    class Args:
        issue_key = "AAP-7"
        text = "test"

    cli.add_comment(Args())
    out = capsys.readouterr().out
    assert "❌ Failed to add comment" in out
