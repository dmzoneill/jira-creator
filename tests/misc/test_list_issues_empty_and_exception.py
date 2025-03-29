from rh_jira import JiraCLI


def test_list_issues_empty(monkeypatch, capsys):
    cli = JiraCLI()
    monkeypatch.setattr(cli.jira, "list_issues", lambda *a, **k: [])

    class Args:
        project = None
        component = None
        user = None

    cli.list(Args())
    out = capsys.readouterr().out
    assert "No issues found." in out


def test_list_issues_fail(monkeypatch, capsys):
    cli = JiraCLI()
    monkeypatch.setattr(
        cli.jira,
        "list_issues",
        lambda *a, **k: (_ for _ in ()).throw(Exception("fail")),
    )

    class Args:
        project = None
        component = None
        user = None

    cli.list(Args())
    out = capsys.readouterr().out
    assert "❌ Failed to list issues" in out
