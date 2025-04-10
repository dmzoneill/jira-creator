from unittest.mock import MagicMock, patch

import pytest
from commands.cli_edit_issue import edit_description, get_prompt

from exceptions.exceptions import (  # isort: skip
    EditDescriptionError,
    EditIssueError,
    GetPromptError,
    UpdateDescriptionError,
)  # isort: skip


@patch("commands.cli_edit_issue.subprocess.call", return_value=0)
@patch("commands.cli_edit_issue.tempfile.NamedTemporaryFile")
def test_edit_issue_update_exception(mock_tmpfile, mock_subprocess, capsys, cli):
    # Mock Jira internals
    cli.jira.get_description = MagicMock(return_value="original")
    cli.jira.get_issue_type = MagicMock(return_value="story")
    cli.jira.update_description = MagicMock(side_effect=UpdateDescriptionError("fail"))

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
        issue_key = "AAP-test_edit_issue_update_exception"
        no_ai = False
        lint = False  # ✅ Add this to fix the error

    with pytest.raises(UpdateDescriptionError):
        cli.edit_issue(Args())

    out = capsys.readouterr().out
    assert "❌ Update failed" in out


def test_edit_description_raises_edit_description_error_inline(capsys):
    with (
        patch("commands.cli_edit_issue.tempfile.NamedTemporaryFile") as mock_tmpfile,
        patch(
            "commands.cli_edit_issue.subprocess.call",
            side_effect=EditDescriptionError("boom!"),
        ),
    ):
        fake_file = MagicMock()
        fake_file.__enter__.return_value = fake_file
        fake_file.name = "/tmp/fake_edit.md"
        fake_file.write = MagicMock()
        fake_file.flush = MagicMock()
        fake_file.seek = MagicMock()
        fake_file.read = MagicMock(return_value="edited text")
        mock_tmpfile.return_value = fake_file

        with pytest.raises(EditDescriptionError) as exc_info:
            edit_description("original description")

        captured = capsys.readouterr()
        assert "❌ Failed to edit description: boom!" in captured.out
        assert "boom!" in str(exc_info.value)


def test_get_prompt_raises_and_falls_back(capsys):
    fake_jira = MagicMock()
    fake_jira.get_issue_type.side_effect = GetPromptError("could not fetch type")
    default_prompt = "This is a fallback prompt."

    with (
        patch("commands.cli_edit_issue.PromptLibrary.get_prompt") as mock_prompt,
        patch("commands.cli_edit_issue.IssueType") as mock_issue_type,
    ):
        result = get_prompt(fake_jira, "TEST-123", default_prompt)

    captured = capsys.readouterr()
    assert result == default_prompt
    assert "❌ Failed to get Jira prompt" in captured.out
    mock_prompt.assert_not_called()
    mock_issue_type.assert_not_called()


def test_cli_edit_issue_raises_edit_issue_error(cli):
    class Args:
        issue_key = "TEST-ERR"
        no_ai = True
        lint = False

    with (
        patch("commands.cli_edit_issue.fetch_description", return_value="some text"),
        patch(
            "commands.cli_edit_issue.edit_description",
            side_effect=EditIssueError("boom!"),
        ),
        patch("commands.cli_edit_issue.get_prompt") as mock_get_prompt,
        patch("commands.cli_edit_issue.update_jira_description") as mock_update,
    ):
        with pytest.raises(EditIssueError) as exc_info:
            cli.edit_issue(Args())

        assert "boom!" in str(exc_info.value)
        mock_get_prompt.assert_not_called()
        mock_update.assert_not_called()
