from jira_creator.rh_jira import JiraCLI
from unittest.mock import MagicMock
import tempfile


def test_edit_no_ai(monkeypatch):
    cli = JiraCLI()
    cli.jira.get_description = lambda k: "description"
    cli.jira.update_description = MagicMock()
    cli.jira.get_issue_type = lambda k: "story"

    with tempfile.NamedTemporaryFile("w+", delete=False) as tf:
        tf.write("edited")
        tf.seek(0)

        class Args:
            issue_key = "AAP-123"
            no_ai = True

        cli.edit_issue(Args())
        cli.jira.update_description.assert_called_once()