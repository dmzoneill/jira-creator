from unittest.mock import MagicMock, patch

import pytest

from jira_creator.rh_jira import JiraCLI


@pytest.fixture
def cli():
    with (
        patch(
            "jira_creator.commands.edit_issue.tempfile.NamedTemporaryFile"
        ) as mock_tempfile,
        patch("jira_creator.commands.edit_issue.subprocess.call", return_value=0),
    ):

        cli = JiraCLI()

        # Mock Jira methods
        cli.jira.get_description = MagicMock(return_value="Original description")
        cli.jira.update_description = MagicMock(return_value=True)
        cli.jira.get_issue_type = MagicMock(return_value="story")

        # Mock AI provider
        cli.ai_provider.improve_text = MagicMock(
            return_value="Cleaned and corrected content."
        )

        # Mock tempfile file behavior
        fake_file = MagicMock()
        fake_file.__enter__.return_value = fake_file
        fake_file.read.return_value = "edited content"
        fake_file.name = "/fake/file.md"
        mock_tempfile.return_value = fake_file

        yield cli


def test_edit_issue_executes(cli):
    args = type("Args", (), {"issue_key": "FAKE-123", "no_ai": False})()
    cli.edit_issue(args)
    cli.jira.update_description.assert_called_once()
