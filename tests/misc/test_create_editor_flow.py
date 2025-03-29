from rh_jira import JiraCLI
import tempfile


def test_create_editor(monkeypatch):
    cli = JiraCLI()
    monkeypatch.setattr("builtins.input", lambda x: "value")
    monkeypatch.setattr(cli.jira, "create_issue", lambda p: "AAP-123")
    monkeypatch.setattr(cli.ai_provider, "improve_text", lambda p, t: t)
    monkeypatch.setattr("subprocess.call", lambda cmd: 0)
    tf = tempfile.NamedTemporaryFile(delete=False, mode="w+")
    tf.write("description")
    tf.flush()
    tf.seek(0)
    monkeypatch.setattr("tempfile.NamedTemporaryFile", lambda *a, **k: tf)

    class Args:
        type = "story"
        summary = "My Summary"
        edit = True
        dry_run = False

    cli.create(Args())
