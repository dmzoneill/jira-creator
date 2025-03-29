from jira_creator.rh_jira import JiraCLI


def test_create_ai_failure(monkeypatch, capsys):
    cli = JiraCLI()
    monkeypatch.setattr(cli.jira, "build_payload", lambda *a, **k: {})
    monkeypatch.setattr(cli.jira, "create_issue", lambda x: "AAP-6")
    monkeypatch.setattr("builtins.input", lambda x: "test")
    monkeypatch.setattr(
        cli.ai_provider,
        "improve_text",
        lambda *a, **k: (_ for _ in ()).throw(Exception("ai fail")),
    )
    monkeypatch.setattr(
        "tempfile.NamedTemporaryFile", lambda *a, **k: open("/tmp/fake_create", "w+")
    )
    monkeypatch.setattr("subprocess.call", lambda cmd: 0)
    monkeypatch.setattr("os.environ", {"EDITOR": "true"})

    class Args:
        type = "story"
        summary = "summary"
        edit = False
        dry_run = True

    with open("/tmp/fake_create", "w") as f:
        f.write("template")
    cli.create(Args())
    out = capsys.readouterr().out
    assert "📦 DRY RUN ENABLED" in out
