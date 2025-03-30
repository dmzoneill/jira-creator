import tempfile
from unittest.mock import MagicMock

from jira_creator.rh_jira import JiraCLI


def test_edit_with_ai(monkeypatch):
    cli = JiraCLI()
    cli.jira.get_description = lambda k: "raw text"
    cli.jira.update_description = MagicMock()
    cli.jira.get_issue_type = lambda k: "story"
    cli.ai_provider.improve_text = lambda p, t: "cleaned text"

    with tempfile.NamedTemporaryFile("w+", delete=False) as tf:
        tf.write("dirty")
        tf.seek(0)

        class Args:
            issue_key = "AAP-999"
            no_ai = False

        cli.edit_issue(Args())
        cli.jira.update_description.assert_called_once_with("AAP-999", "cleaned text")
