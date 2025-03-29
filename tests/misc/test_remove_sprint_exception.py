from rh_jira import JiraCLI


def test_remove_sprint_error(monkeypatch, capsys):
    cli = JiraCLI()
    cli.jira.remove_from_sprint = lambda k: (_ for _ in ()).throw(Exception("fail"))

    class Args:
        issue_key = "AAP-3"

    cli.remove_sprint(Args())
    out = capsys.readouterr().out
    assert "❌ Failed to remove sprint" in out
