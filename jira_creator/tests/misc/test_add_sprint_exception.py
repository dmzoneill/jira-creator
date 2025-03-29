from jira_creator.rh_jira import JiraCLI


def test_add_sprint_exception(monkeypatch, capsys):
    cli = JiraCLI()
    cli.jira.add_to_sprint_by_name = lambda a, b: (_ for _ in ()).throw(
        Exception("fail")
    )

    class Args:
        issue_key = "AAP-1"
        sprint_name = "Sprint X"

    cli.add_sprint(Args())
    out = capsys.readouterr().out
    assert "❌" in out
