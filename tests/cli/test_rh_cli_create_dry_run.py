import os
from rh_jira import JiraCLI
from unittest.mock import MagicMock


def test_create_dry_run(monkeypatch):
    cli = JiraCLI()
    monkeypatch.setattr("builtins.input", lambda _: "Test field")
    monkeypatch.setattr(cli, "jira", MagicMock())
    monkeypatch.setattr(cli, "ai_provider", MagicMock())
    monkeypatch.setattr(
        cli.jira, "build_payload", lambda s, d, t: {"fields": {"summary": s}}
    )
    monkeypatch.setattr(cli.jira, "create_issue", lambda payload: "AAP-123")

    class Args:
        type = "story"
        summary = "Sample summary"
        edit = False
        dry_run = True

    cli.create(Args())
