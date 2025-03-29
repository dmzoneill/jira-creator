import pytest
from jira_creator.rh_jira import JiraCLI


def test_run_register_dispatch(monkeypatch):
    cli = JiraCLI()

    class DummyParser:
        def __init__(self):
            self.commands = {}

    monkeypatch.setattr(
        "argparse.ArgumentParser.add_subparsers", lambda *a, **k: DummyParser()
    )
    monkeypatch.setattr(
        "argparse.ArgumentParser.parse_args",
        lambda self: type("Args", (), {"command": "create"}),
    )
    monkeypatch.setattr("argcomplete.autocomplete", lambda *a, **k: None)
    monkeypatch.setattr(cli, "_register_subcommands", lambda x: None)
    monkeypatch.setattr(cli, "_dispatch_command", lambda args: None)
    cli.run()
