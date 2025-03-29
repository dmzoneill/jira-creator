from jira_creator.rh_jira import JiraCLI
from unittest.mock import MagicMock
import tempfile


def test_edit_with_ai(monkeypatch):
    cli = JiraCLI()
    monkeypatch.setattr(cli.jira, "get_description", lambda k: "raw text")
    monkeypatch.setattr(cli.jira, "update_description", MagicMock())
    monkeypatch.setattr(cli.jira, "get_issue_type", lambda k: "story")
    monkeypatch.setattr(cli.ai_provider, "improve_text", lambda p, t: "cleaned text")

    with tempfile.NamedTemporaryFile("w+", delete=False) as tf:
        tf.write("dirty")
        tf.seek(0)
        monkeypatch.setattr("subprocess.call", lambda *a: 0)
        monkeypatch.setattr("tempfile.NamedTemporaryFile", lambda *a, **kw: tf)

        class Args:
            issue_key = "AAP-999"
            no_ai = False

        cli.edit_issue(Args())
        cli.jira.update_description.assert_called_once_with("AAP-999", "cleaned text")
