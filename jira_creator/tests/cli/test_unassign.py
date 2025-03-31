from jira_creator.rh_jira import JiraCLI


def test_unassign_success(monkeypatch, capsys):
    cli = JiraCLI()
    cli.jira.unassign_issue = lambda k: True

    class Args:
        issue_key = "AAP-42"

    cli.unassign(Args())
    out = capsys.readouterr().out
    assert "✅" in out


def test_unassign_failure(monkeypatch, capsys):
    cli = JiraCLI()
    cli.jira.unassign_issue = lambda k: False

    class Args:
        issue_key = "AAP-42"

    cli.unassign(Args())
    out = capsys.readouterr().out
    assert "❌" in out
