from jira_creator.rh_jira import JiraCLI
import tempfile
import os


def test_add_comment_editor(monkeypatch):
    cli = JiraCLI()
    monkeypatch.setattr(cli.jira, "add_comment", lambda k, v: None)
    monkeypatch.setattr(cli.ai_provider, "improve_text", lambda p, t: t)
    monkeypatch.setenv("EDITOR", "true")

    tf = tempfile.NamedTemporaryFile(delete=False, mode="w+")
    tf.write("my comment")
    tf.flush()
    tf.seek(0)

    monkeypatch.setattr("tempfile.NamedTemporaryFile", lambda *a, **k: tf)
    monkeypatch.setattr("subprocess.call", lambda cmd: 0)

    class Args:
        issue_key = "AAP-1"
        text = None

    cli.add_comment(Args())
