from jira_creator.rh_jira import JiraCLI


def test_set_status_exception(monkeypatch, capsys):
    cli = JiraCLI()
    monkeypatch.setattr(
        cli.jira,
        "set_status",
        lambda *a: (_ for _ in ()).throw(Exception("bad status")),
    )

    class Args:
        issue_key = "AAP-900"
        status = "Invalid"

    cli.set_status(Args())
    out = capsys.readouterr().out
    assert "❌ Failed to update status" in out
