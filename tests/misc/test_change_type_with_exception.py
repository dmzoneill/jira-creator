from rh_jira import JiraCLI


def test_change_type_failure(monkeypatch, capsys):
    cli = JiraCLI()
    monkeypatch.setattr(
        cli.jira,
        "change_issue_type",
        lambda *a, **k: (_ for _ in ()).throw(Exception("Boom")),
    )

    class Args:
        issue_key = "AAP-1"
        new_type = "task"

    cli.change_type(Args())
    out = capsys.readouterr().out
    assert "❌ Error" in out
