from rh_jira import JiraCLI
from unittest.mock import MagicMock
import tempfile


def test_edit_no_ai(monkeypatch):
    cli = JiraCLI()
    monkeypatch.setattr(cli.jira, "get_description", lambda k: "description")
    monkeypatch.setattr(cli.jira, "update_description", MagicMock())
    monkeypatch.setattr(cli.jira, "get_issue_type", lambda k: "story")

    with tempfile.NamedTemporaryFile("w+", delete=False) as tf:
        tf.write("edited")
        tf.seek(0)
        monkeypatch.setattr("subprocess.call", lambda cmd: 0)
        monkeypatch.setattr("tempfile.NamedTemporaryFile", lambda *a, **kw: tf)

        class Args:
            issue_key = "AAP-123"
            no_ai = True

        cli.edit_issue(Args())
        cli.jira.update_description.assert_called_once()
