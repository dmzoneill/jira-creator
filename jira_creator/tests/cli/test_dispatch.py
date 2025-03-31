from jira_creator.rh_jira import JiraCLI


def test_dispatch_unknown_command(monkeypatch):
    cli = JiraCLI()

    class DummyArgs:
        command = "does-not-exist"

    cli._dispatch_command(DummyArgs())  # should print error but not crash
