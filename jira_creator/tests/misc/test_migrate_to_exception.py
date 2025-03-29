from jira_creator.rh_jira import JiraCLI


def test_migrate_to_exception(monkeypatch, capsys):
    cli = JiraCLI()
    monkeypatch.setattr(
        cli.jira, "migrate_issue", lambda *a: (_ for _ in ()).throw(Exception("fail"))
    )
    monkeypatch.setattr(cli.jira, "jira_url", "http://fake")

    class Args:
        issue_key = "AAP-123"
        new_type = "story"

    cli.migrate(Args())
    out = capsys.readouterr().out
    assert "❌ Migration failed" in out
