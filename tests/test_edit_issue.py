import os
import tempfile
import pytest
from unittest.mock import patch, MagicMock
from rh_jira import JiraCLI


@pytest.fixture
def cli(monkeypatch):
    cli = JiraCLI()

    # Patch editor to simulate editing
    monkeypatch.setenv("EDITOR", "true")

    # Mock JiraClient methods
    cli.jira.get_description = MagicMock(return_value="Original description")
    cli.jira.update_description = MagicMock(return_value=True)
    cli.jira._request = MagicMock(
        return_value={"fields": {"issuetype": {"name": "story"}}}
    )

    # Patch tempfile to return edited content
    patched_tempfile = tempfile.NamedTemporaryFile

    def fake_tempfile(*args, **kwargs):
        tmp = patched_tempfile(mode="w+", suffix=".md", delete=False)
        tmp.write("Edited content with mistakes.")
        tmp.flush()
        tmp.seek(0)
        return tmp

    monkeypatch.setattr(tempfile, "NamedTemporaryFile", fake_tempfile)

    # Patch AI provider
    cli.ai_provider.improve_text = MagicMock(
        return_value="Cleaned and corrected content."
    )
    return cli


def test_edit_issue_executes(monkeypatch, cli):
    cli.edit_issue("FAKE-123")
    cli.jira.update_description.assert_called_once()
