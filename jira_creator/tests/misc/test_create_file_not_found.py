import sys
import pytest
from jira_creator.rh_jira import JiraCLI


def test_create_file_not_found(monkeypatch):
    cli = JiraCLI()

    class Args:
        type = "nonexistent"
        summary = "test"
        edit = False
        dry_run = False

    monkeypatch.setattr(
        "rh_jira.TemplateLoader",
        lambda *a, **k: (_ for _ in ()).throw(FileNotFoundError("missing.tmpl")),
    )
    with pytest.raises(SystemExit):
        cli.create(Args())
