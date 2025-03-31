from unittest.mock import MagicMock, patch

from jira_creator.rh_jira import JiraCLI


@patch("jira_creator.commands.edit_issue.subprocess.call", return_value=0)
@patch("jira_creator.commands.edit_issue.tempfile.NamedTemporaryFile")
def test_edit_issue_update_exception(mock_tmpfile, mock_subprocess, capsys):
    cli = JiraCLI()

    # Mock Jira internals
    cli.jira.get_description = MagicMock(return_value="original")
    cli.jira.get_issue_type = MagicMock(return_value="story")
    cli.jira.update_description = MagicMock(side_effect=Exception("fail"))

    # Mock cleanup logic
    cli._try_cleanup = MagicMock(return_value="cleaned")
    cli.ai_provider.improve_text = MagicMock(return_value="cleaned")  # ✅ Important

    # Mock temp file
    fake_file = MagicMock()
    fake_file.__enter__.return_value = fake_file
    fake_file.read.return_value = "edited"
    fake_file.write = MagicMock()
    fake_file.flush = MagicMock()
    fake_file.seek = MagicMock()
    fake_file.name = "/tmp/fake_edit"
    mock_tmpfile.return_value = fake_file

    # Simulated CLI args
    class Args:
        issue_key = "AAP-5"
        no_ai = False

    cli.edit_issue(Args())

    out = capsys.readouterr().out
    assert "❌ Update failed" in out
