from rh_jira import JiraCLI
from jira import jira_prompts


def test_create_value_error_prompt(monkeypatch):
    cli = JiraCLI()

    monkeypatch.setattr(cli.jira, "create_issue", lambda p: "AAP-123")
    monkeypatch.setattr(cli.ai_provider, "improve_text", lambda p, t: t)

    class DummyTemplate:
        def get_fields(self):
            return ["field1"]

        def render_description(self, inputs):
            return "Rendered description"

    monkeypatch.setattr("builtins.input", lambda x: "value")
    monkeypatch.setattr("rh_jira.TemplateLoader", lambda *a, **k: DummyTemplate())

    # simulate unknown issue type causing ValueError
    monkeypatch.setattr(
        jira_prompts,
        "JiraIssueType",
        lambda t: (_ for _ in ()).throw(ValueError("unknown type")),
    )

    class Args:
        type = "unknown"
        summary = "Some summary"
        edit = False
        dry_run = True

    cli.create(Args())
