from jira_creator.rh_jira import JiraCLI


def test_add_comment_ai_fail(monkeypatch, capsys):
    cli = JiraCLI()
    monkeypatch.setattr(cli.jira, "add_comment", lambda k, v: None)
    monkeypatch.setattr(
        cli.ai_provider,
        "improve_text",
        lambda *a, **k: (_ for _ in ()).throw(Exception("fail")),
    )

    class Args:
        issue_key = "AAP-1"
        text = "Comment text"

    cli.add_comment(Args())
    out = capsys.readouterr().out
    assert "⚠️ AI cleanup failed" in out
