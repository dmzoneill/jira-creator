from rh_jira import JiraCLI


def test_dispatch_command_invalid(monkeypatch, capsys):
    cli = JiraCLI()

    class Args:
        command = "nonexistent"

    cli._dispatch_command(Args())
    out = capsys.readouterr().out
    assert "❌ Command failed" in out
