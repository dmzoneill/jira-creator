import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from jira_creator.rh_jira import JiraCLI

# Add project root to PYTHONPATH
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


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
    cli.edit_issue(type("Args", (), {"issue_key": "FAKE-123", "no_ai": False})())
    cli.jira.update_description.assert_called_once()
