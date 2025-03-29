from jira_creator.rh_jira import JiraCLI


def test_create_exception(monkeypatch, capsys):
    cli = JiraCLI()
    monkeypatch.setattr("builtins.input", lambda x: "value")
    monkeypatch.setattr(cli.ai_provider, "improve_text", lambda p, t: t)
    monkeypatch.setattr(
        cli.jira,
        "create_issue",
        lambda *a, **k: (_ for _ in ()).throw(Exception("fail")),
    )

    class DummyTemplate:
        def get_fields(self):
            return ["f"]

        def render_description(self, i):
            return "desc"

    monkeypatch.setattr(
        "templates.template_loader.TemplateLoader", lambda *a, **k: DummyTemplate()
    )

    class Args:
        type = "story"
        summary = "Fail"
        edit = False
        dry_run = False

    cli.create(Args())
    out = capsys.readouterr().out
    assert "❌ Failed to create issue" in out
