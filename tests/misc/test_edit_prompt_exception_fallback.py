from rh_jira import JiraCLI


def test_edit_prompt_exception_fallback(monkeypatch):
    cli = JiraCLI()

    monkeypatch.setattr(cli.jira, "get_description", lambda k: "desc")
    monkeypatch.setattr(
        cli.jira, "get_issue_type", lambda k: (_ for _ in ()).throw(Exception("fail"))
    )
    monkeypatch.setattr(cli.jira, "update_description", lambda k, d: None)
    monkeypatch.setattr(cli.ai_provider, "improve_text", lambda p, t: t)
    monkeypatch.setattr("subprocess.call", lambda cmd: 0)

    class DummyTempFile:
        def __init__(self):
            self.name = "temp.md"

        def write(self, content):
            pass

        def flush(self):
            pass

        def seek(self, n):
            pass

        def read(self):
            return "cleaned"

    monkeypatch.setattr("tempfile.NamedTemporaryFile", lambda *a, **kw: DummyTempFile())

    class Args:
        issue_key = "AAP-1"
        no_ai = False

    cli.edit_issue(Args())
