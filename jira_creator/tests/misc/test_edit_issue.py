from unittest.mock import MagicMock, patch

import pytest

from jira_creator.rh_jira import JiraCLI


@pytest.fixture
def cli():
    # Setup the JiraCLI object
    cli = JiraCLI()

    # Mock JiraClient methods
    cli.jira.get_description = MagicMock(return_value="Original description")
    cli.jira.update_description = MagicMock(return_value=True)

    # Mock AI provider
    cli.ai_provider.improve_text = MagicMock(
        return_value="Cleaned and corrected content."
    )

    # Mock tempfile.NamedTemporaryFile to avoid actual file handling during tests
    with patch("tempfile.NamedTemporaryFile") as mock_tempfile:
        mock_tempfile.return_value.__enter__.return_value.name = "/fake/file.md"
        mock_tempfile.return_value.__enter__.return_value.read.return_value = (
            "edited content"
        )
        cli.jira._tempfile = mock_tempfile
        yield cli


def test_edit_issue_executes(cli):
    # Simulate calling edit_issue with fake arguments
    args = type("Args", (), {"issue_key": "FAKE-123", "no_ai": False})()

    # Call the edit_issue method
    cli.edit_issue(args)

    # Ensure that update_description was called
    cli.jira.update_description.assert_called_once()

    # If you still get the I/O error, it likely means the file isn't being handled correctly.
    # Add assertions or print statements in the edit_issue method to track the file access flow.
