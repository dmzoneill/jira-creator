from rh_jira import JiraCLI


def test_edit_issue_update_exception(monkeypatch, capsys):
    cli = JiraCLI()
    monkeypatch.setattr(cli.jira, "get_description", lambda k: "original")
    monkeypatch.setattr(cli.jira, "get_issue_type", lambda k: "story")
    monkeypatch.setattr(
        cli.jira,
        "update_description",
        lambda k, v: (_ for _ in ()).throw(Exception("fail")),
    )
    monkeypatch.setattr(cli, "_try_cleanup", lambda p, t: t)
    monkeypatch.setattr(
        "tempfile.NamedTemporaryFile", lambda *a, **kw: open("/tmp/fake_edit", "w+")
    )
    monkeypatch.setattr("subprocess.call", lambda cmd: 0)

    with open("/tmp/fake_edit", "w") as f:
        f.write("edited")

    class Args:
        issue_key = "AAP-5"
        no_ai = False

    cli.edit_issue(Args())
    out = capsys.readouterr().out
    assert "❌ Update failed" in out
