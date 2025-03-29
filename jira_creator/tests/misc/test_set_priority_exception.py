from jira_creator.rh_jira import JiraCLI


def test_set_priority_error(monkeypatch, capsys):
    cli = JiraCLI()
    cli.jira.set_priority = lambda k, p: (_ for _ in ()).throw(Exception("fail"))

    class Args:
        issue_key = "AAP-4"
        priority = "High"

    cli.set_priority(Args())
    out = capsys.readouterr().out
    assert "❌ Failed to set priority" in out
