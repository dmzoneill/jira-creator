from jira_creator.rh_jira import JiraCLI
from unittest.mock import MagicMock
import tempfile


def test_edit_issue_update_exception(capsys):
    cli = JiraCLI()

    # Mocking Jira methods
    cli.jira.get_description = MagicMock(return_value="original")
    cli.jira.get_issue_type = MagicMock(return_value="story")
    cli.jira.update_description = MagicMock(side_effect=Exception("fail"))

    # Mock _try_cleanup method
    cli._try_cleanup = MagicMock(return_value="cleaned")

    # Mock tempfile.NamedTemporaryFile to simulate file creation
    tempfile.NamedTemporaryFile = MagicMock(return_value=open("/tmp/fake_edit", "w+"))

    # Simulating the file write
    with open("/tmp/fake_edit", "w") as f:
        f.write("edited")

    class Args:
        issue_key = "AAP-5"
        no_ai = False

    cli.edit_issue(Args())
    out = capsys.readouterr().out
    assert "❌ Update failed" in out
